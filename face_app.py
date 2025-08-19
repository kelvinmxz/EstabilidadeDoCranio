from flask import Flask, Response, jsonify, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2
import pyttsx3
import threading
import atexit
import os
import numpy as np
from PIL import Image
import io
import base64
import queue
import time
from face_detection import FacePartDetector

# Inicializa o Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Cria pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Função para limpar recursos
def cleanup():
    global cap, fala_queue
    if cap and cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    
    # Para o worker de fala
    if fala_queue:
        fala_queue.put(None)  # Sinal para parar
    
    print("🧹 Recursos liberados")

# Registra função de limpeza
atexit.register(cleanup)

# Carrega o modelo YOLOv8 (apenas objetos básicos)
print("📊 Carregando modelo YOLOv8...")
model = YOLO('yolov8n.pt')
print("✅ Modelo carregado com sucesso!")

# Dicionário de tradução para português (básico)
traducao_objetos = {
    'person': 'pessoa',
    'car': 'carro',
    'phone': 'celular',
    'laptop': 'notebook',
    'book': 'livro',
    'chair': 'cadeira',
    'bottle': 'garrafa',
    'cup': 'xícara'
}

def traduzir_objeto(nome_ingles):
    """Traduz o nome do objeto para português"""
    return traducao_objetos.get(nome_ingles.lower(), nome_ingles)

# Função para inicializar webcam
def init_webcam():
    global cap, webcam_available
    print("📷 Tentando inicializar webcam...")
    cap = None
    webcam_available = False

    # Tenta diferentes backends
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    
    for backend in backends:
        for i in range(4):  # Tenta índices 0 a 3
            try:
                test_cap = cv2.VideoCapture(i, backend)
                if test_cap.isOpened():
                    # Tenta ler um frame para verificar se realmente funciona
                    ret, frame = test_cap.read()
                    if ret and frame is not None and frame.size > 0:
                        cap = test_cap
                        webcam_available = True
                        print(f"✅ Webcam encontrada no índice {i} com backend {backend}")
                        # Configura propriedades da câmera
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        return True
                    else:
                        test_cap.release()
            except Exception as e:
                print(f"❌ Erro ao tentar índice {i} com backend {backend}: {e}")
                if 'test_cap' in locals():
                    test_cap.release()
        
        if webcam_available:
            break

    if not webcam_available:
        print("❌ Nenhuma webcam funcional encontrada")
        print("📸 Modo apenas upload de imagem ativado")
    
    return webcam_available

# Inicializa a webcam
init_webcam()

# Inicializa o detector de partes do rosto
face_detector = FacePartDetector()
print("👁️ Detector de partes do rosto inicializado!")

# Configura o motor de fala (text-to-speech)
engine = None
fala_queue = queue.Queue()
fala_thread = None
fala_ativa = False

def inicializar_tts():
    global engine
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        # Procura por voz em português
        voz_portugues = None
        if voices:
            for voice in voices:
                voice_name = voice.name.lower()
                voice_id = voice.id.lower()
                # Procura por indicadores de português brasileiro
                if any(indicator in voice_name for indicator in ['portuguese', 'brazil', 'brasil', 'pt-br', 'pt_br']):
                    voz_portugues = voice.id
                    print(f"🇧🇷 Voz em português encontrada: {voice.name}")
                    break
                elif any(indicator in voice_id for indicator in ['portuguese', 'brazil', 'brasil', 'pt-br', 'pt_br']):
                    voz_portugues = voice.id
                    print(f"🇧🇷 Voz em português encontrada: {voice.name}")
                    break
        
        # Se encontrou voz em português, usa ela
        if voz_portugues:
            engine.setProperty('voice', voz_portugues)
        else:
            print("⚠️ Voz em português não encontrada, usando voz padrão")
            # Usa a primeira voz disponível
            if voices:
                engine.setProperty('voice', voices[0].id)
        
        # Configurações adicionais para melhor performance
        engine.setProperty('rate', 170)  # Velocidade da fala um pouco mais rápida
        engine.setProperty('volume', 1.0)  # Volume máximo
        print("🔊 TTS inicializado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Erro ao inicializar TTS: {e}")
        print("O sistema funcionará sem áudio")
        engine = None
        return False

def worker_fala():
    """Thread worker para processar fila de fala"""
    global fala_ativa
    while True:
        try:
            texto = fala_queue.get(timeout=1)
            if texto is None:  # Sinal para parar
                break
                
            if engine:
                fala_ativa = True
                
                # Se o texto já está em português (como descrições), não traduz
                if any(palavra in texto.lower() for palavra in ['há', 'não', 'objetos', 'imagem', 'rosto', 'olho', 'nariz']):
                    texto_fala = texto
                else:
                    texto_fala = traduzir_objeto(texto)
                
                print(f"🔊 Falando: {texto_fala}")
                
                try:
                    # Cria um novo engine para cada fala para evitar conflitos
                    temp_engine = pyttsx3.init()
                    temp_engine.setProperty('rate', 170)
                    temp_engine.setProperty('volume', 1.0)
                    temp_engine.say(texto_fala)
                    temp_engine.runAndWait()
                    temp_engine.stop()
                    del temp_engine
                    print("✅ Fala concluída")
                except Exception as e:
                    print(f"⚠️ Erro ao falar '{texto}': {e}")
                
                fala_ativa = False
            else:
                if any(palavra in texto.lower() for palavra in ['há', 'não', 'objetos', 'imagem', 'rosto', 'olho', 'nariz']):
                    texto_fala = texto
                else:
                    texto_fala = traduzir_objeto(texto)
                print(f"🔊 {texto_fala} (áudio não disponível)")
                
            fala_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Erro no worker de fala: {e}")
            fala_ativa = False

# Inicializa TTS e worker
if inicializar_tts():
    fala_thread = threading.Thread(target=worker_fala, daemon=True)
    fala_thread.start()

# Variáveis globais
ultimo_objeto = None
objetos_detectados = []
current_image = None
partes_rosto_detectadas = []

# Função para falar o nome do objeto/parte do rosto
def falar_nome(nome):
    """Adiciona texto à fila de fala"""
    if not fala_queue.full():
        try:
            # Limpa a fila se tiver muitos itens
            if fala_queue.qsize() > 2:
                while not fala_queue.empty():
                    try:
                        fala_queue.get_nowait()
                    except queue.Empty:
                        break
            
            fala_queue.put(nome)
            print(f"📝 Adicionado à fila de fala: {nome}")
        except Exception as e:
            print(f"❌ Erro ao adicionar à fila: {e}")
    else:
        print("⚠️ Fila de fala cheia, ignorando pedido")

# Função para descrever o rosto
def descrever_rosto(partes, expressoes=None):
    descricao_parts = []
    
    # Descreve partes do rosto
    if not partes:
        descricao_parts.append("Nenhum rosto detectado")
    else:
        if 'rosto' in partes:
            count_olhos = len([p for p in partes if 'olho' in p])
            if count_olhos > 0:
                descricao_parts.append(f"Rosto detectado com {count_olhos} olho{'s' if count_olhos > 1 else ''}")
            else:
                descricao_parts.append("Rosto detectado")
            
            outras_partes = [p for p in partes if p not in ['rosto', 'olho esquerdo', 'olho direito']]
            if outras_partes:
                descricao_parts.append(f"Partes visíveis: {', '.join(outras_partes)}")
    
    # Descreve expressões
    if expressoes:
        descricao_parts.append(f"Expressão: {', '.join(expressoes)}")
    
    return ". ".join(descricao_parts) + "."

# Função para processar imagem (webcam ou upload) - FOCO NO ROSTO
def process_image(frame):
    global ultimo_objeto, objetos_detectados, partes_rosto_detectadas, face_detector
    
    try:
        # Detecção de objetos (bem simplificada)
        results = model(frame, conf=0.5)
        
        h, w = frame.shape[:2]
        center_frame = (w // 2, h // 2)

        min_dist = float('inf')
        closest_box = None
        closest_info = None

        # Limpa listas
        objetos_detectados.clear()
        partes_rosto_detectadas.clear()

        # Processa detecção de objetos (muito simplificada)
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    largura_bbox = x2 - x1
                    altura_bbox = y2 - y1
                    
                    if largura_bbox < 50 or altura_bbox < 50:
                        continue

                    cls = int(box.cls[0])
                    name = model.names[cls]
                    conf = float(box.conf[0])

                    # Só adiciona objetos importantes
                    if name in ['person', 'laptop', 'phone', 'book', 'chair']:
                        objetos_detectados.append(name)

                        box_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                        dist = ((box_center[0] - center_frame[0]) ** 2 + 
                                (box_center[1] - center_frame[1]) ** 2) ** 0.5

                        if dist < min_dist:
                            min_dist = dist
                            closest_box = (x1, y1, x2, y2)
                            closest_info = (name, conf, box_center)

        # *** PROCESSAMENTO PRINCIPAL: DETECÇÃO DE PARTES DO ROSTO ***
        face_parts, expressions = face_detector.detect_face_parts(frame)
        
        # Adiciona partes do rosto detectadas
        if face_parts:
            partes_rosto_detectadas.extend(face_parts)

        # Desenha informações do rosto na tela
        frame = face_detector.draw_info_overlay(frame)

        # Desenha objeto mais próximo (muito discreto)
        if closest_box and closest_info:
            x1, y1, x2, y2 = closest_box
            name, conf, box_center = closest_info
            name_pt = traduzir_objeto(name)
            
            # Desenha de forma muito discreta
            cv2.rectangle(frame, (x1, y1), (x2, y2), (60, 60, 60), 1)
            cv2.putText(frame, f"{name_pt}", (x1, y2+15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (60, 60, 60), 1)
            ultimo_objeto = name

        return frame
    except Exception as e:
        print(f"❌ Erro no processamento da imagem: {e}")
        return frame

# Gera os frames da webcam com detecção de rosto
def gen_frames():
    global current_image, cap, webcam_available
    
    # Se não há webcam e nem imagem carregada, mostra placeholder
    if not webcam_available and current_image is None:
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(placeholder, "Nenhuma webcam disponivel", (150, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(placeholder, "Carregue uma imagem abaixo", (170, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        ret, buffer = cv2.imencode('.jpg', placeholder)
        if ret:
            frame_bytes = buffer.tobytes()
            while True:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                import time
                time.sleep(1)
        return
    
    while True:
        frame = None
        
        # Prioriza imagem carregada sobre webcam
        if current_image is not None:
            frame = current_image.copy()
        elif webcam_available and cap and cap.isOpened():
            try:
                success, frame = cap.read()
                if not success or frame is None:
                    print("❌ Erro ao ler frame da webcam, tentando reconectar...")
                    # Tenta reconectar webcam
                    if init_webcam():
                        continue
                    else:
                        webcam_available = False
                        continue
            except Exception as e:
                print(f"❌ Erro na webcam: {e}")
                webcam_available = False
                continue
        
        if frame is not None:
            try:
                # Processa a imagem
                frame = process_image(frame)
                
                # Codifica o frame
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    print("❌ Erro ao codificar frame")
                    
            except Exception as e:
                print(f"❌ Erro ao processar frame: {e}")
                continue
        
        # Pequena pausa para não sobrecarregar
        import time
        time.sleep(0.03)  # ~30 FPS

# Rota principal com interface HTML
@app.route('/')
def index():
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Detector de Partes do Rosto</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            #video-container {{
                display: inline-block;
                border: 3px solid #fff;
                padding: 10px;
                background: white;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }}
            #objeto_nome {{
                margin-top: 20px;
                font-size: 20px;
                color: #fff;
                font-weight: bold;
                background: rgba(255,255,255,0.1);
                padding: 10px;
                border-radius: 10px;
            }}
            #partes_rosto {{
                margin-top: 15px;
                font-size: 18px;
                color: #ffeb3b;
                font-weight: bold;
                background: rgba(255,235,59,0.2);
                padding: 15px;
                border-radius: 10px;
            }}
            button {{
                margin: 10px;
                padding: 15px 25px;
                font-size: 16px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                font-weight: bold;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            }}
            .upload-section {{
                margin: 20px 0;
                padding: 20px;
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                border: 2px dashed #fff;
            }}
            input[type="file"] {{
                margin: 10px;
                padding: 10px;
                background: white;
                border-radius: 5px;
                color: black;
            }}
            .status {{
                margin: 15px 0;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
            }}
            .success {{ 
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
            }}
            .warning {{ 
                background: linear-gradient(45deg, #ff9800, #f57c00);
                color: white;
            }}
            .face-guide {{
                background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
                padding: 20px;
                border-radius: 15px;
                margin: 15px 0;
                border: 2px solid rgba(255,255,255,0.3);
                backdrop-filter: blur(10px);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👁️ Detector de Partes do Rosto</h1>
            
            <div class="status {'success' if webcam_available else 'warning'}">
                {'📷 Webcam ativa - Detecção de rosto em tempo real' if webcam_available else '📸 Modo upload - Carregue uma imagem para análise'}
            </div>
            
            <div class="face-guide">
                <h3>👁️ Partes do Rosto Detectáveis:</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; text-align: left; margin: 15px 0;">
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <p style="margin: 8px 0;"><span style="color: #2196f3; font-size: 20px;">🔵</span> <strong>ROSTO</strong> - Contorno facial</p>
                        <p style="margin: 8px 0;"><span style="color: #4caf50; font-size: 20px;">🟢</span> <strong>OLHO ESQUERDO</strong></p>
                        <p style="margin: 8px 0;"><span style="color: #ffeb3b; font-size: 20px;">🟡</span> <strong>OLHO DIREITO</strong></p>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <p style="margin: 8px 0;"><span style="color: #00bcd4; font-size: 20px;">🔷</span> <strong>NARIZ</strong> - Centro do rosto</p>
                        <p style="margin: 8px 0;"><span style="color: #e91e63; font-size: 20px;">🟣</span> <strong>BOCA/SORRISO</strong></p>
                        <p style="margin: 8px 0;"><span style="color: #ff9800; font-size: 20px;">🟠</span> <strong>SOBRANCELHAS</strong></p>
                    </div>
                </div>
                <p style="margin-top: 15px; color: #ffeb3b; text-align: center; font-weight: bold; font-size: 18px;">
                    🎯 Cada parte será destacada com cores diferentes quando detectada!
                </p>
            </div>
            
            {'<div class="upload-section"><h3>📁 Carregar Imagem</h3><form method="POST" action="/upload" enctype="multipart/form-data"><input type="file" name="file" accept="image/*" required><button type="submit">Enviar Imagem</button></form></div>' if not webcam_available or True else ''}
            
            <div id="video-container">
                <img src="/video" width="640" height="480" alt="Feed de vídeo" />
            </div>
            
            <div id="objeto_nome">Nenhum objeto detectado</div>
            <div id="partes_rosto">👀 Posicione seu rosto na frente da câmera</div>
            
            <div>
                <button onclick="capturar()">🔊 Falar Objeto (Espaço)</button>
                <button onclick="falarPartes()">👁️ Falar Partes do Rosto</button>
                <button onclick="descrever()">💬 Descrever Tudo</button>
                <button onclick="reconectarWebcam()">🔄 Reconectar Webcam</button>
                {'<button onclick="trocarCamera()">🔄 Trocar Webcam/Upload</button>' if webcam_available else ''}
            </div>
        </div>

        <script>
            // Detecta tecla Espaço
            document.addEventListener('keydown', function(e) {{
                if (e.code === 'Space') {{
                    e.preventDefault();
                    capturar();
                }}
            }});

            // Envia requisição para falar e atualizar texto
            function capturar() {{
                fetch('/falar', {{ method: 'POST' }})
                    .then(() => fetch('/objeto'))
                    .then(r => r.json())
                    .then(data => {{
                        const texto = data.nome ? "Objeto capturado: " + data.nome_pt : "Nenhum objeto detectado";
                        document.getElementById('objeto_nome').innerText = texto;
                    }})
                    .catch(error => {{
                        console.error('Erro:', error);
                        document.getElementById('objeto_nome').innerText = "Erro ao capturar objeto";
                    }});
            }}

            // Fala as partes do rosto detectadas
            function falarPartes() {{
                fetch('/partes_rosto')
                    .then(r => r.json())
                    .then(data => {{
                        if (data.partes && data.partes.length > 0) {{
                            const partesTexto = data.partes.join(', ');
                            fetch('/falar', {{ 
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ texto: `Detectado: ${{partesTexto}}` }})
                            }});
                            document.getElementById('partes_rosto').innerText = `👁️ Detectado: ${{partesTexto}}`;
                        }} else {{
                            document.getElementById('partes_rosto').innerText = "👀 Nenhuma parte do rosto detectada";
                            fetch('/falar', {{ 
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ texto: "Nenhuma parte do rosto detectada" }})
                            }});
                        }}
                    }})
                    .catch(error => {{
                        console.error('Erro:', error);
                        document.getElementById('partes_rosto').innerText = "Erro ao detectar partes do rosto";
                    }});
            }}

            // Descreve tudo
            function descrever() {{
                fetch('/descrever', {{ method: 'POST' }})
                    .then(r => r.json())
                    .then(data => {{
                        alert(data.descricao);
                        document.getElementById('partes_rosto').innerText = data.descricao;
                    }})
                    .catch(error => {{
                        console.error('Erro:', error);
                        alert('Erro ao descrever');
                    }});
            }}

            function trocarCamera() {{
                fetch('/toggle_mode', {{ method: 'POST' }})
                    .then(() => location.reload());
            }}

            function reconectarWebcam() {{
                document.getElementById('objeto_nome').innerText = "Tentando reconectar webcam...";
                fetch('/reconnect_webcam', {{ method: 'POST' }})
                    .then(r => r.json())
                    .then(data => {{
                        if (data.success) {{
                            document.getElementById('objeto_nome').innerText = "✅ Webcam reconectada com sucesso!";
                            setTimeout(() => location.reload(), 1000);
                        }} else {{
                            document.getElementById('objeto_nome').innerText = "❌ Não foi possível conectar à webcam";
                        }}
                    }})
                    .catch(error => {{
                        console.error('Erro:', error);
                        document.getElementById('objeto_nome').innerText = "❌ Erro ao tentar reconectar";
                    }});
            }}

            // Atualização automática
            setInterval(() => {{
                // Atualiza objetos
                fetch('/objeto')
                    .then(r => r.json())
                    .then(data => {{
                        const texto = data.nome ? "Último objeto: " + data.nome_pt : "Nenhum objeto detectado";
                        document.getElementById('objeto_nome').innerText = texto;
                    }})
                    .catch(() => {{}});
                
                // Atualiza partes do rosto
                fetch('/partes_rosto')
                    .then(r => r.json())
                    .then(data => {{
                        if (data.partes && data.partes.length > 0) {{
                            const partesTexto = data.partes.join(', ').toUpperCase();
                            document.getElementById('partes_rosto').innerText = `👁️ ${{partesTexto}}`;
                            document.getElementById('partes_rosto').style.color = '#4caf50';
                            document.getElementById('partes_rosto').style.fontWeight = 'bold';
                        }} else {{
                            document.getElementById('partes_rosto').innerText = "👀 Posicione seu rosto na frente da câmera";
                            document.getElementById('partes_rosto').style.color = '#ffeb3b';
                            document.getElementById('partes_rosto').style.fontWeight = 'normal';
                        }}
                    }})
                    .catch(() => {{}});
            }}, 2000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html, webcam_available=webcam_available)

# Upload de arquivo
@app.route('/upload', methods=['POST'])
def upload_file():
    global current_image
    
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file:
        try:
            # Lê a imagem diretamente da memória
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            # Converte para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Converte PIL para OpenCV
            current_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Redimensiona se muito grande
            h, w = current_image.shape[:2]
            if w > 800:
                scale = 800 / w
                new_w = int(w * scale)
                new_h = int(h * scale)
                current_image = cv2.resize(current_image, (new_w, new_h))
            
            print(f"✅ Imagem carregada: {file.filename}")
            
        except Exception as e:
            print(f"❌ Erro ao processar imagem: {e}")
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

# Streaming de vídeo
@app.route('/video')
def video():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Retorna o último objeto detectado
@app.route('/objeto')
def objeto():
    global ultimo_objeto
    if ultimo_objeto:
        nome_pt = traduzir_objeto(ultimo_objeto)
        return jsonify({"nome": ultimo_objeto, "nome_pt": nome_pt})
    else:
        return jsonify({"nome": None, "nome_pt": None})

# Retorna partes do rosto detectadas
@app.route('/partes_rosto')
def partes_rosto():
    global partes_rosto_detectadas
    return jsonify({"partes": partes_rosto_detectadas})

# Rota que faz o TTS
@app.route('/falar', methods=['POST'])
def falar():
    global ultimo_objeto
    
    # Verifica se há texto customizado no corpo da requisição
    try:
        data = request.get_json()
        if data and 'texto' in data:
            texto_customizado = data['texto']
            falar_nome(texto_customizado)
            return jsonify({"falando": True, "texto": texto_customizado})
    except:
        pass  # Se não conseguir ler JSON, continua com comportamento padrão
    
    # Comportamento padrão - fala o objeto detectado
    if ultimo_objeto:
        falar_nome(ultimo_objeto)
        return jsonify({"falando": True, "objeto": traduzir_objeto(ultimo_objeto)})
    else:
        return jsonify({"falando": False, "objeto": None})

# Rota que descreve tudo
@app.route('/descrever', methods=['POST'])
def descrever():
    global objetos_detectados, partes_rosto_detectadas
    info_rosto = face_detector.get_face_info()
    descricao = descrever_rosto(info_rosto['parts'], info_rosto['expressions'])
    falar_nome(descricao)
    return jsonify({"descricao": descricao, "partes": info_rosto['parts']})

# Rota para trocar entre webcam e upload
@app.route('/toggle_mode', methods=['POST'])
def toggle_mode():
    global current_image
    current_image = None
    return '', 204

# Rota para verificar status da webcam
@app.route('/webcam_status')
def webcam_status():
    global webcam_available
    return jsonify({"webcam_available": webcam_available})

# Rota para tentar reconectar webcam
@app.route('/reconnect_webcam', methods=['POST'])
def reconnect_webcam():
    global current_image
    current_image = None  # Remove imagem carregada
    success = init_webcam()
    return jsonify({"success": success, "webcam_available": webcam_available})

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
