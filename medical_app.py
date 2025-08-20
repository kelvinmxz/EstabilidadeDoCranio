from flask import Flask, Response, jsonify, render_template_string, request
import cv2
import pyttsx3
import threading
import atexit
import numpy as np
import queue
import time
from medical_head_stability import MedicalHeadStabilityAnalyzer

# Inicializa o Flask
app = Flask(__name__)

# Função para limpar recursos
def cleanup():
    global cap, fala_queue, analyzer
    if cap and cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    
    # Para o worker de fala
    if fala_queue:
        fala_queue.put(None)
    
    print("🧹 Recursos liberados")

# Registra função de limpeza
atexit.register(cleanup)

# Configuração do TTS
print("🔊 Configurando sistema de voz...")
fala_queue = queue.Queue()

def configurar_tts():
    """Configura o sistema text-to-speech"""
    engine = pyttsx3.init()
    
    # Configurações de voz em português
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'brazil' in voice.name.lower() or 'portuguese' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            print(f"🇧🇷 Voz em português encontrada: {voice.name}")
            break
    
    # Configurações
    engine.setProperty('rate', 150)  # Velocidade
    engine.setProperty('volume', 0.8)  # Volume
    
    return engine

def worker_fala():
    """Worker thread para processamento de fala"""
    engine = configurar_tts()
    
    while True:
        try:
            texto = fala_queue.get(timeout=1)
            if texto is None:  # Sinal para parar
                break
            engine.say(texto)
            engine.runAndWait()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Erro no TTS: {e}")

# Inicia worker de fala
fala_thread = threading.Thread(target=worker_fala, daemon=True)
fala_thread.start()
print("🔊 TTS inicializado com sucesso")

# Inicializa webcam
print("📹 Inicializando sistema de câmera...")
cap = None

# Tenta diferentes índices de câmera
for i in range(3):
    test_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if test_cap.isOpened():
        ret, frame = test_cap.read()
        if ret and frame is not None:
            cap = test_cap
            print(f"✅ Webcam encontrada no índice {i}")
            break
        test_cap.release()

if cap is None:
    print("❌ Nenhuma webcam encontrada")
    cap = cv2.VideoCapture(0)

# Configurações da câmera
if cap.isOpened():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    print("📹 Câmera configurada: 1280x720 @ 30fps")

# Inicializa o analisador médico
print("🏥 Inicializando Sistema Médico de Estabilidade...")
analyzer = MedicalHeadStabilityAnalyzer(
    stability_threshold=8,      # Movimento máximo permitido (pixels)
    time_threshold=3.0,         # Tempo necessário de estabilidade (segundos)
    sensitivity='medium'        # Sensibilidade: 
)
print("✅ Sistema Médico inicializado!")

# Variáveis de controle
procedure_started = False
last_announcement = 0
announcement_interval = 10  # Anunciar a cada 10 segundos quando pronto

def process_frame(frame):
    """Processa o frame para análise médica"""
    global procedure_started, last_announcement
    
    # Analisa estabilidade
    is_ready = analyzer.analyze_stability(frame)
    
    # Desenha informações de estabilidade
    frame_with_info = analyzer.draw_stability_info(frame)
    
    # Controle de anúncios de voz
    current_time = time.time()
    
    if is_ready and not procedure_started:
        if current_time - last_announcement > announcement_interval:
            fala_queue.put("Paciente estável. Sistema pronto para iniciar procedimento médico.")
            last_announcement = current_time
    
    elif analyzer.is_stable and not is_ready:
        if current_time - last_announcement > announcement_interval:
            fala_queue.put("Paciente em posição. Mantendo estabilidade.")
            last_announcement = current_time
    
    elif not analyzer.is_stable:
        # Reset do timer se perdeu estabilidade
        last_announcement = 0
    
    return frame_with_info

def gen_frames():
    """Gera frames para streaming"""
    while True:
        success, frame = cap.read()
        if not success:
            print("❌ Falha ao capturar frame")
            break
        
        # Processa o frame
        processed_frame = process_frame(frame)
        
        # Converte para JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame, 
                                  [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Template HTML médico profissional
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema Médico de Estabilidade da Cabeça</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .medical-header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-bottom: 3px solid #2c5aa0;
        }
        
        .medical-header h1 {
            color: #2c5aa0;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .medical-header .subtitle {
            color: #666;
            font-size: 1.2em;
            margin-bottom: 15px;
        }
        
        .medical-badges {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .badge {
            background: #2c5aa0;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .video-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .video-container {
            text-align: center;
            margin-bottom: 20px;
        }
        
        #videoFeed {
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border: 3px solid #2c5aa0;
        }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .control-panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .control-panel h3 {
            color: #2c5aa0;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .btn {
            background: #2c5aa0;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: all 0.3s ease;
            width: 100%;
            margin: 5px 0;
        }
        
        .btn:hover {
            background: #1e3d6f;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        .btn.success {
            background: #27ae60;
        }
        
        .btn.success:hover {
            background: #219a52;
        }
        
        .btn.warning {
            background: #f39c12;
        }
        
        .btn.warning:hover {
            background: #e67e22;
        }
        
        .btn.danger {
            background: #e74c3c;
        }
        
        .btn.danger:hover {
            background: #c0392b;
        }
        
        .status-info {
            margin-top: 20px;
        }
        
        .status-card {
            background: #f8f9fa;
            border-left: 4px solid #2c5aa0;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        
        .status-ready {
            border-left-color: #27ae60;
            background: #d5f4e6;
        }
        
        .status-stable {
            border-left-color: #f39c12;
            background: #fef9e7;
        }
        
        .status-unstable {
            border-left-color: #e74c3c;
            background: #fdf2f2;
        }
        
        .medical-info {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        
        .medical-info h3 {
            color: #2c5aa0;
            margin-bottom: 15px;
        }
        
        .medical-info ul {
            list-style: none;
            padding-left: 0;
        }
        
        .medical-info li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .medical-info li:before {
            content: "✓";
            color: #27ae60;
            font-weight: bold;
            margin-right: 10px;
        }
        
        @media (max-width: 768px) {
            .medical-header h1 {
                font-size: 2em;
            }
            
            .medical-badges {
                flex-direction: column;
                align-items: center;
            }
            
            .controls {
                grid-template-columns: 1fr;
            }
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9em;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            animation: fadeIn 0.3s;
        }

        .modal-content {
            background-color: #fefefe;
            margin: 10% auto;
            padding: 30px;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
        }

        .modal-header {
            color: #2c5aa0;
            margin-bottom: 20px;
        }

        .modal-warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }

        .modal-danger {
            background: #f8d7da;
            border: 1px solid #dc3545;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #721c24;
        }

        .modal-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 25px;
        }

        .modal-btn {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .modal-btn.confirm {
            background: #28a745;
            color: white;
        }

        .modal-btn.confirm:hover {
            background: #218838;
        }

        .modal-btn.cancel {
            background: #6c757d;
            color: white;
        }

        .modal-btn.cancel:hover {
            background: #545b62;
        }

        .modal-btn.danger {
            background: #dc3545;
            color: white;
        }

        .modal-btn.danger:hover {
            background: #c82333;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="medical-header">
        <h1>🏥 Sistema Médico de Estabilidade da Cabeça</h1>
        <p class="subtitle">Monitoramento em Tempo Real para Procedimentos de Imagem</p>
        <div class="medical-badges">
            <span class="badge">Ressonância Magnética</span>
            <span class="badge">Tomografia Computadorizada</span>
            <span class="badge">Radiografia Craniana</span>
        </div>
    </div>

    <div class="container">
        <div class="video-section">
            <h3 style="color: #2c5aa0; text-align: center; margin-bottom: 20px;">
                📹 Monitoramento de Estabilidade em Tempo Real
            </h3>
            <div class="video-container">
                <img id="videoFeed" src="{{ url_for('video_feed') }}" alt="Feed da Câmera">
            </div>
        </div>

        <div class="controls">
            <div class="control-panel">
                <h3>🎛️ Controles do Sistema</h3>
                
                <!-- 🔵 BOTÃO DE TESTE PARA DEBUG -->
                <button class="btn" onclick="testButton()" style="background: #ff9800; color: white; margin-bottom: 10px;">
                    🔍 TESTE JAVASCRIPT
                </button>
                
                <button class="btn success" onclick="console.log('Botão Iniciar clicado!'); startProcedure()">
                    ▶️ Iniciar Procedimento
                </button>
                <button class="btn warning" onclick="console.log('Botão Status clicado!'); getStatus()">
                    📊 Status Atual
                </button>
                <button class="btn" onclick="console.log('Botão Reiniciar clicado!'); resetAnalysis()">
                    🔄 Reiniciar Análise
                </button>
                <button class="btn danger" onclick="console.log('Botão Parar clicado!'); stopProcedure()">
                    ⏹️ Parar Procedimento
                </button>
            </div>

            <div class="control-panel">
                <h3>📊 Configurações</h3>
                <label>Sensibilidade:</label>
                <select id="sensitivity" onchange="updateSensitivity()" class="btn" style="margin-top: 10px;">
                    <option value="high">Alta (5px)</option>
                    <option value="medium" selected>Média (10px)</option>
                    <option value="low">Baixa (20px)</option>
                </select>
                
                <label style="margin-top: 15px; display: block;">Tempo de Estabilidade:</label>
                <select id="timeThreshold" onchange="updateTimeThreshold()" class="btn" style="margin-top: 5px;">
                    <option value="2">2 segundos</option>
                    <option value="3" selected>3 segundos</option>
                    <option value="5">5 segundos</option>
                    <option value="10">10 segundos</option>
                </select>
            </div>
        </div>

        <div class="status-info">
            <div id="statusDisplay" class="status-card">
                <strong>Status:</strong> <span id="currentStatus">Inicializando sistema...</span>
            </div>
        </div>

        <div class="medical-info">
            <h3>🏥 Procedimentos Compatíveis</h3>
            <ul>
                <li><strong>Ressonância Magnética do Crânio:</strong> Evita artefatos de movimento nas imagens cerebrais</li>
                <li><strong>Tomografia Computadorizada:</strong> Garante precisão nas imagens seccionais</li>
                <li><strong>Radiografia Craniana:</strong> Previne imagens borradas em estruturas ósseas</li>
                <li><strong>Procedimentos Neurológicos:</strong> Suporte para pacientes com dificuldades motoras</li>
            </ul>
        </div>
    </div>

    <div class="footer">
        <p>MXZ -<i>Feito por Kelvin Costa Maués</i></p>
    </div>

    <!-- Modal de Confirmação -->
    <div id="confirmationModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">⚠️ Confirmação de Procedimento</h2>
            </div>
            <div id="modalMessage">
                <p>Deseja iniciar o procedimento mesmo com o paciente não estando na condição ideal?</p>
            </div>
            <div id="modalWarning" class="modal-warning" style="display: none;">
                <strong>⚠️ ATENÇÃO:</strong> Paciente estável mas tempo de estabilização incompleto. 
                Qualidade da imagem pode ser ligeiramente comprometida.
            </div>
            <div id="modalDanger" class="modal-danger" style="display: none;">
                <strong>🚨 RISCO ALTO:</strong> Paciente instável. Alto risco de:
                <ul style="text-align: left; margin-top: 10px;">
                    <li>Imagens borradas ou com artefatos</li>
                    <li>Necessidade de repetição do exame</li>
                    <li>Comprometimento do diagnóstico</li>
                    <li>Desperdício de tempo e recursos</li>
                </ul>
            </div>
            <div class="modal-buttons">
                <button id="modalCancel" class="modal-btn cancel">❌ Cancelar</button>
                <button id="modalConfirm" class="modal-btn confirm">✅ Confirmar</button>
                <button id="modalForceStart" class="modal-btn danger" style="display: none;">⚠️ Iniciar com Risco</button>
            </div>
        </div>
    </div>

    <script>
        let procedureActive = false;
        let statusInterval;

        // 🔵 FUNÇÃO DE TESTE PARA DEBUG
        function testButton() {
            console.log('🔵 TESTE: Função testButton executada!');
            alert('✅ JavaScript está funcionando!');
        }

        function startProcedure(forceStart = false) {
            if (procedureActive) {
                alert('Procedimento já está ativo!');
                return;
            }
            
            const requestData = forceStart ? { force_start: true } : {};
            
            fetch('/start_procedure', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        procedureActive = true;
                        let statusMessage = '🟢 Procedimento iniciado';
                        
                        if (data.status === 'yellow') {
                            statusMessage = '🟡 Procedimento iniciado (estável)';
                        } else if (data.status === 'red') {
                            statusMessage = '� Procedimento iniciado (RISCO)';
                        }
                        
                        updateStatus(statusMessage + ' - Monitorando estabilidade');
                        startStatusMonitoring();
                        
                        if (data.warning) {
                            alert('⚠️ ATENÇÃO: Procedimento iniciado com risco aumentado!');
                        }
                    } else {
                        // Mostra modal de confirmação se necessário
                        if (data.allow_force) {
                            showConfirmationModal(data);
                        } else {
                            alert('Erro ao iniciar procedimento: ' + data.message);
                        }
                    }
                });
        }

        function showConfirmationModal(data) {
            const modal = document.getElementById('confirmationModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalMessage = document.getElementById('modalMessage');
            const modalWarning = document.getElementById('modalWarning');
            const modalDanger = document.getElementById('modalDanger');
            const modalConfirm = document.getElementById('modalConfirm');
            const modalForceStart = document.getElementById('modalForceStart');
            
            // Reset modal
            modalWarning.style.display = 'none';
            modalDanger.style.display = 'none';
            modalConfirm.style.display = 'inline-block';
            modalForceStart.style.display = 'none';
            
            if (data.status === 'yellow') {
                // Paciente estável mas tempo incompleto
                modalTitle.textContent = '⚠️ Paciente Estável - Confirmar Início';
                modalMessage.innerHTML = '<p>O paciente está estável, mas ainda não completou o tempo mínimo de estabilização.</p>';
                modalWarning.style.display = 'block';
                modalConfirm.textContent = '✅ Iniciar Procedimento';
            } else if (data.status === 'red') {
                // Paciente instável - risco alto
                modalTitle.textContent = '🚨 ATENÇÃO - Paciente Instável';
                modalMessage.innerHTML = '<p><strong>RISCO ELEVADO:</strong> O paciente está se movimentando e não está estável.</p>';
                modalDanger.style.display = 'block';
                modalConfirm.style.display = 'none';
                modalForceStart.style.display = 'inline-block';
                modalForceStart.textContent = '⚠️ Iniciar com Risco';
            }
            
            modal.style.display = 'block';
        }

        function hideConfirmationModal() {
            document.getElementById('confirmationModal').style.display = 'none';
        }

        // Event listeners do modal
        document.getElementById('modalCancel').addEventListener('click', hideConfirmationModal);
        
        document.getElementById('modalConfirm').addEventListener('click', function() {
            hideConfirmationModal();
            startProcedure(true);
        });
        
        document.getElementById('modalForceStart').addEventListener('click', function() {
            if (confirm('⚠️ CONFIRMAÇÃO FINAL: Tem certeza que deseja iniciar o procedimento com o paciente instável?\n\nISTO PODE RESULTAR EM:\n• Imagens de baixa qualidade\n• Necessidade de repetir o exame\n• Risco para o diagnóstico')) {
                hideConfirmationModal();
                startProcedure(true);
            }
        });

        // Fechar modal clicando fora
        window.addEventListener('click', function(event) {
            const modal = document.getElementById('confirmationModal');
            if (event.target === modal) {
                hideConfirmationModal();
            }
        });

        function stopProcedure() {
            fetch('/stop_procedure', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    procedureActive = false;
                    updateStatus('🔴 Procedimento interrompido');
                    stopStatusMonitoring();
                });
        }

        function getStatus() {
            fetch('/get_status')
                .then(response => response.json())
                .then(data => {
                    let statusClass = 'status-card';
                    if (data.is_ready) {
                        statusClass += ' status-ready';
                    } else if (data.is_stable) {
                        statusClass += ' status-stable';
                    } else {
                        statusClass += ' status-unstable';
                    }
                    
                    document.getElementById('statusDisplay').className = statusClass;
                    updateStatus(data.message + ` (Estabilidade: ${data.stability_score.toFixed(1)}%)`);
                });
        }

        function resetAnalysis() {
            fetch('/reset_analysis', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateStatus('🔄 Análise reiniciada');
                });
        }

        function updateSensitivity() {
            const sensitivity = document.getElementById('sensitivity').value;
            fetch('/update_sensitivity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sensitivity: sensitivity })
            });
        }

        function updateTimeThreshold() {
            const timeThreshold = parseFloat(document.getElementById('timeThreshold').value);
            fetch('/update_time_threshold', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ time_threshold: timeThreshold })
            });
        }

        function updateStatus(message) {
            document.getElementById('currentStatus').textContent = message;
        }

        function startStatusMonitoring() {
            statusInterval = setInterval(getStatus, 1000); // Atualiza a cada segundo
        }

        function stopStatusMonitoring() {
            if (statusInterval) {
                clearInterval(statusInterval);
            }
        }

        // Inicia monitoramento automático
        window.onload = function() {
            getStatus();
            startStatusMonitoring();
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Página principal"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """Feed de vídeo"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_procedure', methods=['POST'])
def start_procedure():
    """Inicia procedimento médico com diferentes níveis de validação"""
    global procedure_started
    
    print("🔵 DEBUG: Botão 'Iniciar Procedimento' clicado!")
    
    data = request.get_json() or {}
    force_start = data.get('force_start', False)
    
    print(f"🔵 DEBUG: force_start = {force_start}")
    print(f"🔵 DEBUG: is_ready = {analyzer.is_ready_for_procedure}")
    print(f"🔵 DEBUG: is_stable = {analyzer.is_stable}")
    
    # Verifica status atual
    if analyzer.is_ready_for_procedure:
        # Verde - Pronto para procedimento
        procedure_started = True
        fala_queue.put("Procedimento médico iniciado. Paciente em posição ideal.")
        print("🟢 DEBUG: Procedimento iniciado - Verde")
        return jsonify({
            'success': True, 
            'message': 'Procedimento iniciado - Paciente estável',
            'status': 'green'
        })
    
    elif analyzer.is_stable:
        # Amarelo - Estável mas ainda não pelo tempo completo
        if force_start:
            procedure_started = True
            fala_queue.put("Procedimento iniciado com paciente estável. Monitorando movimento.")
            print("🟡 DEBUG: Procedimento iniciado - Amarelo (forçado)")
            return jsonify({
                'success': True, 
                'message': 'Procedimento iniciado - Paciente estável (tempo reduzido)',
                'status': 'yellow'
            })
        else:
            print("🟡 DEBUG: Solicitando confirmação - Amarelo")
            return jsonify({
                'success': False, 
                'message': 'Paciente estável - Confirmar início?',
                'status': 'yellow',
                'allow_force': True
            })
    
    else:
        # Vermelho - Instável
        if force_start:
            procedure_started = True
            fala_queue.put("Atenção: Procedimento iniciado com paciente instável. Risco aumentado.")
            print("🔴 DEBUG: Procedimento iniciado - Vermelho (forçado)")
            return jsonify({
                'success': True, 
                'message': 'ATENÇÃO: Procedimento iniciado com risco - Paciente instável',
                'status': 'red',
                'warning': True
            })
        else:
            print("🔴 DEBUG: Solicitando confirmação - Vermelho")
            return jsonify({
                'success': False, 
                'message': 'Paciente instável - Início com risco',
                'status': 'red',
                'allow_force': True,
                'risk_warning': True
            })

@app.route('/stop_procedure', methods=['POST'])
def stop_procedure():
    """Para procedimento médico"""
    global procedure_started
    print("🛑 DEBUG: Botão 'Parar Procedimento' clicado!")
    procedure_started = False
    fala_queue.put("Procedimento médico interrompido.")
    return jsonify({'success': True, 'message': 'Procedimento interrompido'})

@app.route('/get_status')
def get_status():
    """Retorna status atual do sistema"""
    print("📊 DEBUG: Botão 'Status Atual' clicado!")
    report = analyzer.get_stability_report()
    report['procedure_active'] = procedure_started
    return jsonify(report)

@app.route('/reset_analysis', methods=['POST'])
def reset_analysis():
    """Reinicia análise"""
    global procedure_started
    print("🔄 DEBUG: Botão 'Reiniciar Análise' clicado!")
    procedure_started = False
    analyzer.reset_analysis()
    fala_queue.put("Sistema reiniciado.")
    return jsonify({'success': True, 'message': 'Análise reiniciada'})

@app.route('/update_sensitivity', methods=['POST'])
def update_sensitivity():
    """Atualiza sensibilidade do sistema"""
    data = request.json
    sensitivity = data.get('sensitivity', 'medium')
    
    # Recria analyzer com nova sensibilidade
    global analyzer
    analyzer = MedicalHeadStabilityAnalyzer(
        stability_threshold=analyzer.stability_threshold,
        time_threshold=analyzer.time_threshold,
        sensitivity=sensitivity
    )
    
    fala_queue.put(f"Sensibilidade alterada para {sensitivity}")
    return jsonify({'success': True, 'sensitivity': sensitivity})

@app.route('/update_time_threshold', methods=['POST'])
def update_time_threshold():
    """Atualiza tempo de estabilidade necessário"""
    data = request.json
    time_threshold = data.get('time_threshold', 3.0)
    
    analyzer.time_threshold = time_threshold
    fala_queue.put(f"Tempo de estabilidade alterado para {time_threshold} segundos")
    return jsonify({'success': True, 'time_threshold': time_threshold})

if __name__ == '__main__':
    print("🏥 Sistema Médico de Estabilidade da Cabeça")
    print("🌐 Acesse: http://127.0.0.1:5000")
    print("📋 Procedimentos suportados:")
    print("   • Ressonância Magnética do Crânio")
    print("   • Tomografia Computadorizada da Cabeça")
    print("   • Radiografia da Cabeça (Raio-X)")
    print("=" * 50)
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
