#!/usr/bin/env python3
"""
Sistema Médico Profissional de Monitoramento de Estabilidade da Cabeça
Versão: 2.0 - Professional Edition
Autor: Sistema Médico IA
Data: 2025

Aplicação: Monitoramento de estabilidade da cabeça durante exames médicos:
- Ressonância Magnética do Crânio
- Tomografia Computadorizada da Cabeça  
- Radiografia da Cabeça (Raio-X)
"""

from flask import Flask, Response, jsonify, render_template_string, request
import cv2
import numpy as np
import threading
import time
import json
from datetime import datetime, timedelta
import queue
import pyttsx3
from medical_head_stability import MedicalHeadStabilityAnalyzer
from medical_configs import get_procedure_config

app = Flask(__name__)

# ===== CONFIGURAÇÕES GLOBAIS =====
camera = None
analyzer = None
fala_queue = queue.Queue()
tts_engine = None
system_status = {
    'procedure_active': False,
    'start_time': None,
    'elapsed_time': 0,
    'current_status': 'Aguardando Paciente',
    'stability_level': 'unknown',
    'procedure_name': 'ressonancia_magnetica',
    'patient_population': 'adulto',
    'sensitivity': 'medium',
    'warnings': []
}

def init_tts():
    """Inicializa sistema de Text-to-Speech"""
    global tts_engine
    try:
        print("🔊 Configurando sistema de voz...")
        tts_engine = pyttsx3.init()
        
        voices = tts_engine.getProperty('voices')
        for voice in voices:
            if 'portuguese' in voice.name.lower() or 'brazil' in voice.name.lower():
                tts_engine.setProperty('voice', voice.id)
                print(f"🇧🇷 Voz em português encontrada: {voice.name}")
                break
        
        tts_engine.setProperty('rate', 150)
        tts_engine.setProperty('volume', 0.8)
        print("🔊 TTS inicializado com sucesso")
        
        # Thread para processar fala
        def process_speech():
            while True:
                try:
                    text = fala_queue.get(timeout=1)
                    if text:
                        tts_engine.say(text)
                        tts_engine.runAndWait()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"❌ Erro no TTS: {e}")
        
        speech_thread = threading.Thread(target=process_speech, daemon=True)
        speech_thread.start()
        
    except Exception as e:
        print(f"❌ Erro ao inicializar TTS: {e}")

def init_camera():
    """Inicializa câmera"""
    global camera
    try:
        print("📹 Inicializando sistema de câmera...")
        
        # Tenta diferentes índices de câmera
        for camera_index in [0, 1, 2]:
            try:
                camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # DSHOW no Windows
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if camera.isOpened():
                    # Testa se consegue ler um frame
                    ret, frame = camera.read()
                    if ret and frame is not None:
                        print(f"✅ Webcam encontrada no índice {camera_index}")
                        
                        # Configura resolução
                        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        camera.set(cv2.CAP_PROP_FPS, 30)
                        
                        print("📹 Câmera configurada: 1280x720 @ 30fps")
                        return
                    else:
                        camera.release()
                else:
                    camera.release()
            except Exception as e:
                print(f"❌ Erro no índice {camera_index}: {e}")
                if camera:
                    camera.release()
                    camera = None
        
        print("⚠️ Nenhuma câmera funcional encontrada - continuando sem câmera")
        camera = None
        
    except Exception as e:
        print(f"❌ Erro ao inicializar câmera: {e}")
        camera = None

def init_analyzer():
    """Inicializa analisador de estabilidade"""
    global analyzer
    try:
        print("🏥 Inicializando Sistema Médico de Estabilidade...")
        
        analyzer = MedicalHeadStabilityAnalyzer(
            stability_threshold=5,
            time_threshold=3.0,
            sensitivity='high'
        )
        print("✅ Sistema Médico inicializado!")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar analisador: {e}")
        # Criar um analisador básico se falhar
        analyzer = MedicalHeadStabilityAnalyzer()

def generate_frames():
    """Gera frames do vídeo com análise"""
    global camera, analyzer, system_status
    
    while True:
        try:
            if camera is None:
                # Cria frame placeholder se não há câmera
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, 'CAMERA NAO DISPONIVEL', (150, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                ret, buffer = cv2.imencode('.jpg', placeholder)
                frame_bytes = buffer.tobytes()
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                time.sleep(0.1)
                continue
                
            success, frame = camera.read()
            if not success:
                continue
                
            if analyzer is None:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                continue
            
            # Análise da estabilidade
            analysis_result = analyzer.analyze_stability(frame)
            
            # Atualiza status do sistema
            if analyzer:
                if analyzer.is_stable:
                    system_status['stability_level'] = 'green' if analyzer.is_ready_for_procedure else 'yellow'
                else:
                    system_status['stability_level'] = 'red'
                
                # Atualiza tempo decorrido se procedimento ativo
                if system_status['procedure_active'] and system_status['start_time']:
                    elapsed = datetime.now() - system_status['start_time']
                    system_status['elapsed_time'] = int(elapsed.total_seconds())
            
            # Desenha overlay no frame
            frame_with_overlay = draw_medical_overlay(frame, analyzer)
            
            ret, buffer = cv2.imencode('.jpg', frame_with_overlay)
            frame_bytes = buffer.tobytes()
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            
        except Exception as e:
            print(f"❌ Erro na geração de frames: {e}")
            time.sleep(0.1)
            continue

def draw_medical_overlay(frame, analyzer):
    """Desenha overlay médico profissional no frame"""
    h, w = frame.shape[:2]
    
    if not analyzer:
        # Se não há análise, mostra status "Analisando"
        cv2.rectangle(frame, (10, 10), (300, 70), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (300, 70), (100, 100, 100), 2)
        cv2.putText(frame, '🔄 ANALISANDO...', (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
        return frame
    
    # Determina status e cor baseado no analisador
    if analyzer.is_ready_for_procedure:
        status_text = '🟢 PACIENTE ESTÁVEL - PRONTO'
        status_color = (0, 255, 0)
        indicator_text = "✅ PRONTO PARA EXAME"
        indicator_color = (0, 255, 0)
    elif analyzer.is_stable:
        status_text = '🟡 ESTABILIZANDO...'
        status_color = (0, 255, 255)
        indicator_text = "⚠️ AGUARDE - ESTABILIZANDO"
        indicator_color = (0, 255, 255)
    else:
        status_text = '� PACIENTE INSTÁVEL'
        status_color = (0, 0, 255)
        indicator_text = "� PACIENTE DEVE PARAR DE SE MOVER"
        indicator_color = (0, 0, 255)
    
    # Fundo do status - canto superior esquerdo
    cv2.rectangle(frame, (10, 10), (400, 70), (0, 0, 0), -1)
    cv2.rectangle(frame, (10, 10), (400, 70), status_color, 3)
    cv2.putText(frame, status_text, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    
    # Informações adicionais
    if hasattr(analyzer, 'stability_score'):
        score_text = f"Estabilidade: {analyzer.stability_score:.1f}%"
        cv2.putText(frame, score_text, (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Timer do procedimento - canto superior direito
    if system_status['procedure_active']:
        timer_text = f"⏱️ PROCEDIMENTO: {format_time(system_status['elapsed_time'])}"
        timer_bg = (w-400, 10, w-10, 70)
        cv2.rectangle(frame, (timer_bg[0], timer_bg[1]), (timer_bg[2], timer_bg[3]), (0, 0, 0), -1)
        cv2.rectangle(frame, (timer_bg[0], timer_bg[1]), (timer_bg[2], timer_bg[3]), (0, 255, 0), 3)
        cv2.putText(frame, timer_text, (timer_bg[0]+10, timer_bg[1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "ATIVO", (timer_bg[0]+10, timer_bg[1]+55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Indicador de estabilidade no centro inferior
    stability_indicator_y = h - 80
    
    # Fundo do indicador central
    text_size = cv2.getTextSize(indicator_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
    indicator_x = (w - text_size[0]) // 2
    cv2.rectangle(frame, (indicator_x-20, stability_indicator_y-20), 
                  (indicator_x + text_size[0] + 20, stability_indicator_y + 20), (0, 0, 0), -1)
    cv2.rectangle(frame, (indicator_x-20, stability_indicator_y-20), 
                  (indicator_x + text_size[0] + 20, stability_indicator_y + 20), indicator_color, 3)
    cv2.putText(frame, indicator_text, (indicator_x, stability_indicator_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, indicator_color, 2)
    
    return frame

def format_time(seconds):
    """Formata tempo em MM:SS"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

# ===== ROTAS FLASK =====

@app.route('/')
def index():
    """Página principal do sistema médico"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """Stream de vídeo com análise"""
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_procedure', methods=['POST'])
def start_procedure():
    """Inicia procedimento médico"""
    global system_status
    
    try:
        data = request.get_json() or {}
        force_start = data.get('force_start', False)
        
        if system_status['procedure_active']:
            return jsonify({'success': False, 'message': 'Procedimento já está ativo'})
        
        current_stability = system_status['stability_level']
        
        # Verifica se pode iniciar baseado no analisador
        can_start = False
        if analyzer:
            if analyzer.is_ready_for_procedure or force_start:
                can_start = True
            elif analyzer.is_stable and force_start:
                can_start = True
        elif force_start:
            can_start = True
        
        if can_start:
            system_status['procedure_active'] = True
            system_status['start_time'] = datetime.now()
            system_status['elapsed_time'] = 0
            system_status['current_status'] = 'Procedimento em Andamento'
            
            # Feedback por voz
            if analyzer and analyzer.is_ready_for_procedure:
                fala_queue.put("Procedimento médico iniciado. Paciente estável.")
            else:
                fala_queue.put("Procedimento iniciado com paciente instável. Monitorando.")
            
            return jsonify({
                'success': True,
                'status': current_stability,
                'message': 'Procedimento iniciado com sucesso',
                'warning': not (analyzer and analyzer.is_ready_for_procedure)
            })
        
        else:
            # Retorna opção de forçar início
            return jsonify({
                'success': False,
                'allow_force': True,
                'status': current_stability,
                'message': 'Paciente não está completamente estável'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/stop_procedure', methods=['POST'])
def stop_procedure():
    """Para procedimento médico"""
    global system_status
    
    try:
        if not system_status['procedure_active']:
            return jsonify({'success': False, 'message': 'Nenhum procedimento ativo'})
        
        # Calcula tempo total
        if system_status['start_time']:
            elapsed = datetime.now() - system_status['start_time']
            total_time = int(elapsed.total_seconds())
        else:
            total_time = 0
        
        system_status['procedure_active'] = False
        system_status['start_time'] = None
        system_status['elapsed_time'] = 0
        system_status['current_status'] = 'Procedimento Finalizado'
        
        # Feedback por voz
        fala_queue.put(f"Procedimento finalizado. Duração: {format_time(total_time)}")
        
        return jsonify({
            'success': True,
            'message': 'Procedimento finalizado',
            'total_time': total_time,
            'formatted_time': format_time(total_time)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Atualiza configurações do sistema"""
    global system_status, analyzer
    
    try:
        data = request.get_json() or {}
        
        # Atualiza tipo de procedimento
        if 'procedure_type' in data:
            system_status['procedure_name'] = data['procedure_type']
        
        # Atualiza sensibilidade
        if 'sensitivity' in data:
            system_status['sensitivity'] = data['sensitivity']
            
            # Reinicializa analisador com nova sensibilidade
            if analyzer:
                if data['sensitivity'] == 'high':
                    analyzer.stability_threshold = 3
                    analyzer.time_threshold = 2.0
                elif data['sensitivity'] == 'medium':
                    analyzer.stability_threshold = 8
                    analyzer.time_threshold = 3.0
                else:  # low
                    analyzer.stability_threshold = 15
                    analyzer.time_threshold = 4.0
                
                # Reset do histórico para aplicar nova configuração
                analyzer.reset_analysis()
        
        return jsonify({'success': True, 'message': 'Configurações atualizadas'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/get_status', methods=['GET'])
def get_status():
    """Retorna status atual do sistema"""
    global system_status, analyzer
    
    # Atualiza status com informações do analisador se disponível
    if analyzer:
        if analyzer.is_ready_for_procedure:
            system_status['stability_level'] = 'green'
        elif analyzer.is_stable:
            system_status['stability_level'] = 'yellow'
        else:
            system_status['stability_level'] = 'red'
            
        system_status['stability_score'] = analyzer.stability_score
        system_status['message'] = analyzer.message
    
    return jsonify(system_status)

# ===== TEMPLATE HTML =====

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
            color: #333;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            color: white;
        }
        
        .header h1 {
            color: white;
            margin-bottom: 0.5rem;
            font-size: 2.2rem;
        }
        
        .header p {
            color: #ecf0f1;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        
        .procedure-badge {
            background: rgba(52, 152, 219, 0.9);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            display: inline-block;
            margin-top: 0.5rem;
        }
        
        .main-container {
            display: flex;
            gap: 2rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .video-section {
            flex: 2;
        }
        
        .video-container {
            background: #fff;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .video-stream {
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .control-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .config-panel {
            background: #fff;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .config-panel h3 {
            color: #2c3e50;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        
        .config-group {
            margin-bottom: 1rem;
        }
        
        .config-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
            color: #34495e;
        }
        
        .config-select {
            width: 100%;
            padding: 0.8rem;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1rem;
            background: white;
            transition: border-color 0.3s ease;
        }
        
        .config-select:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .sensitivity-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        
        .sensitivity-level {
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-weight: bold;
            text-align: center;
            opacity: 0.3;
            transition: all 0.3s ease;
        }
        
        .sensitivity-high {
            background: #e74c3c;
            color: white;
        }
        
        .sensitivity-medium {
            background: #f39c12;
            color: white;
        }
        
        .sensitivity-low {
            background: #27ae60;
            color: white;
        }
        
        .sensitivity-active {
            opacity: 1;
            transform: scale(1.1);
        }
        
        .status-panel {
            background: #fff;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .status-panel h3 {
            color: #2c3e50;
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        
        .status-display {
            text-align: center;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 10px;
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        .status-waiting {
            background: #f8f9fa;
            color: #6c757d;
            border: 2px dashed #dee2e6;
        }
        
        .status-active {
            background: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }
        
        .status-completed {
            background: #cce7ff;
            color: #004085;
            border: 2px solid #99d3ff;
        }
        
        .timer-display {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            padding: 1rem;
            margin: 1rem 0;
            background: #f8f9fa;
            border-radius: 10px;
            color: #2c3e50;
        }
        
        .control-buttons {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .btn {
            padding: 1rem 1.5rem;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn-start {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
        }
        
        .btn-stop {
            background: linear-gradient(135deg, #dc3545, #e83e8c);
            color: white;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }
        
        .stability-indicator {
            display: flex;
            justify-content: space-around;
            margin: 1rem 0;
        }
        
        .stability-level {
            text-align: center;
            padding: 0.5rem;
            border-radius: 8px;
            font-weight: bold;
            width: 30%;
        }
        
        .level-green {
            background: #d4edda;
            color: #155724;
        }
        
        .level-yellow {
            background: #fff3cd;
            color: #856404;
        }
        
        .level-red {
            background: #f8d7da;
            color: #721c24;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.7);
        }
        
        .modal-content {
            background-color: #fff;
            margin: 10% auto;
            padding: 2rem;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .modal-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        }
        
        .modal-btn {
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .modal-btn-confirm {
            background: #28a745;
            color: white;
        }
        
        .modal-btn-cancel {
            background: #6c757d;
            color: white;
        }
        
        .modal-btn-danger {
            background: #dc3545;
            color: white;
        }
        
        @media (max-width: 768px) {
            .main-container {
                flex-direction: column;
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Sistema Médico de Estabilidade da Cabeça</h1>
        <p>Monitoramento Profissional para Exames de Imagem</p>
        <div class="procedure-badge" id="procedureBadge">
            📋 Ressonância Magnética do Crânio
        </div>
    </div>
    
    <div class="main-container">
        <div class="video-section">
            <div class="video-container">
                <img src="/video_feed" alt="Video Stream" class="video-stream">
            </div>
        </div>
        
        <div class="control-section">
            <div class="config-panel">
                <h3>⚙️ Configurações do Exame</h3>
                
                <div class="config-group">
                    <label for="procedureSelect">Tipo de Procedimento:</label>
                    <select id="procedureSelect" class="config-select" onchange="updateProcedure()">
                        <option value="ressonancia_magnetica">🧠 Ressonância Magnética do Crânio</option>
                        <option value="tomografia_computadorizada">💀 Tomografia Computadorizada</option>
                        <option value="radiografia_craniana">📷 Radiografia da Cabeça (Raio-X)</option>
                        <option value="angiografia_cerebral">🩸 Angiografia Cerebral</option>
                        <option value="pet_scan">⚛️ PET Scan Cerebral</option>
                        <option value="ultrassom_craniano">🔊 Ultrassom Craniano</option>
                    </select>
                </div>
                
                <div class="config-group">
                    <label for="sensitivitySelect">Sensibilidade de Movimento:</label>
                    <select id="sensitivitySelect" class="config-select" onchange="updateSensitivity()">
                        <option value="high">🔴 Alta (Exames críticos - RM, TC)</option>
                        <option value="medium" selected>🟡 Média (Exames padrão)</option>
                        <option value="low">🟢 Baixa (Raio-X, exames rápidos)</option>
                    </select>
                    <div class="sensitivity-indicator">
                        <span class="sensitivity-level sensitivity-high" id="highLevel">ALTA</span>
                        <span class="sensitivity-level sensitivity-medium sensitivity-active" id="mediumLevel">MÉDIA</span>
                        <span class="sensitivity-level sensitivity-low" id="lowLevel">BAIXA</span>
                    </div>
                </div>
            </div>
            
            <div class="status-panel">
                <h3>📊 Status do Sistema</h3>
                <div id="statusDisplay" class="status-display status-waiting">
                    Aguardando Paciente
                </div>
                <div id="timerDisplay" class="timer-display">
                    00:00
                </div>
                <div class="stability-indicator">
                    <div class="stability-level level-green">🟢 ESTÁVEL</div>
                    <div class="stability-level level-yellow">🟡 ESTABILIZANDO</div>
                    <div class="stability-level level-red">🔴 INSTÁVEL</div>
                </div>
            </div>
            
            <div class="status-panel">
                <h3>🎛️ Controles</h3>
                <div class="control-buttons">
                    <button id="startBtn" class="btn btn-start">
                        ▶️ Iniciar Procedimento
                    </button>
                    <button id="stopBtn" class="btn btn-stop" disabled>
                        ⏹️ Finalizar Procedimento
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal de Confirmação -->
    <div id="confirmModal" class="modal">
        <div class="modal-content">
            <h3 id="modalTitle">Confirmar Procedimento</h3>
            <p id="modalMessage"></p>
            <div class="modal-buttons">
                <button id="modalCancel" class="modal-btn modal-btn-cancel">❌ Cancelar</button>
                <button id="modalConfirm" class="modal-btn modal-btn-confirm">✅ Confirmar</button>
                <button id="modalForce" class="modal-btn modal-btn-danger" style="display: none;">⚠️ Forçar Início</button>
            </div>
        </div>
    </div>
    
    <script>
        let procedureActive = false;
        let startTime = null;
        let timerInterval = null;
        
        // Elementos DOM
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusDisplay = document.getElementById('statusDisplay');
        const timerDisplay = document.getElementById('timerDisplay');
        const modal = document.getElementById('confirmModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalMessage = document.getElementById('modalMessage');
        const modalCancel = document.getElementById('modalCancel');
        const modalConfirm = document.getElementById('modalConfirm');
        const modalForce = document.getElementById('modalForce');
        const procedureBadge = document.getElementById('procedureBadge');
        
        // Configurações
        const procedureSelect = document.getElementById('procedureSelect');
        const sensitivitySelect = document.getElementById('sensitivitySelect');
        
        // Event Listeners
        startBtn.addEventListener('click', startProcedure);
        stopBtn.addEventListener('click', stopProcedure);
        modalCancel.addEventListener('click', closeModal);
        modalConfirm.addEventListener('click', confirmStart);
        modalForce.addEventListener('click', forceStart);
        
        // 🔧 FUNÇÕES DE CONFIGURAÇÃO
        function updateProcedure() {
            const selectedValue = procedureSelect.value;
            const procedureNames = {
                'ressonancia_magnetica': '🧠 Ressonância Magnética do Crânio',
                'tomografia_computadorizada': '💀 Tomografia Computadorizada',
                'radiografia_craniana': '📷 Radiografia da Cabeça (Raio-X)',
                'angiografia_cerebral': '🩸 Angiografia Cerebral',
                'pet_scan': '⚛️ PET Scan Cerebral',
                'ultrassom_craniano': '🔊 Ultrassom Craniano'
            };
            
            procedureBadge.textContent = '📋 ' + procedureNames[selectedValue];
            
            // Atualiza configurações no servidor
            fetch('/update_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ procedure_type: selectedValue })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Procedimento atualizado:', selectedValue);
                }
            })
            .catch(error => console.error('Erro ao atualizar procedimento:', error));
        }
        
        function updateSensitivity() {
            const selectedValue = sensitivitySelect.value;
            
            // Atualiza indicadores visuais
            document.querySelectorAll('.sensitivity-level').forEach(el => {
                el.classList.remove('sensitivity-active');
            });
            
            if (selectedValue === 'high') {
                document.getElementById('highLevel').classList.add('sensitivity-active');
            } else if (selectedValue === 'medium') {
                document.getElementById('mediumLevel').classList.add('sensitivity-active');
            } else {
                document.getElementById('lowLevel').classList.add('sensitivity-active');
            }
            
            // Atualiza configurações no servidor
            fetch('/update_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sensitivity: selectedValue })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Sensibilidade atualizada:', selectedValue);
                    // Mostra feedback visual temporário
                    showSensitivityFeedback(selectedValue);
                }
            })
            .catch(error => console.error('Erro ao atualizar sensibilidade:', error));
        }
        
        function showSensitivityFeedback(level) {
            const messages = {
                'high': '🔴 Sensibilidade ALTA ativa - Detecta movimentos mínimos',
                'medium': '🟡 Sensibilidade MÉDIA ativa - Detecta movimentos normais',
                'low': '🟢 Sensibilidade BAIXA ativa - Tolera movimentos maiores'
            };
            
            // Cria notificação temporária
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #2c3e50;
                color: white;
                padding: 1rem;
                border-radius: 8px;
                z-index: 1001;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                transition: all 0.3s ease;
            `;
            notification.textContent = messages[level];
            
            document.body.appendChild(notification);
            
            // Remove após 3 segundos
            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
        
        function startProcedure() {
            fetch('/start_procedure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    activateProcedure();
                } else if (data.allow_force) {
                    showConfirmModal(data);
                } else {
                    alert('Erro: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao comunicar com servidor');
            });
        }
        
        function stopProcedure() {
            fetch('/stop_procedure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    deactivateProcedure(data.formatted_time);
                } else {
                    alert('Erro: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao comunicar com servidor');
            });
        }
        
        function activateProcedure() {
            procedureActive = true;
            startTime = Date.now();
            
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            statusDisplay.textContent = '🟢 Procedimento em Andamento';
            statusDisplay.className = 'status-display status-active';
            
            startTimer();
        }
        
        function deactivateProcedure(totalTime) {
            procedureActive = false;
            startTime = null;
            
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            statusDisplay.textContent = `✅ Procedimento Finalizado - Duração: ${totalTime}`;
            statusDisplay.className = 'status-display status-completed';
            
            stopTimer();
            
            setTimeout(() => {
                resetInterface();
            }, 5000);
        }
        
        function resetInterface() {
            statusDisplay.textContent = 'Aguardando Paciente';
            statusDisplay.className = 'status-display status-waiting';
            timerDisplay.textContent = '00:00';
        }
        
        function startTimer() {
            timerInterval = setInterval(() => {
                if (startTime) {
                    const elapsed = Math.floor((Date.now() - startTime) / 1000);
                    timerDisplay.textContent = formatTime(elapsed);
                }
            }, 1000);
        }
        
        function stopTimer() {
            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }
        }
        
        function formatTime(seconds) {
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        
        function showConfirmModal(data) {
            if (data.status === 'yellow') {
                modalTitle.textContent = '⚠️ Paciente Estável - Confirmar';
                modalMessage.textContent = 'O paciente está estável mas ainda não completou o tempo mínimo. Deseja prosseguir?';
                modalConfirm.style.display = 'inline-block';
                modalForce.style.display = 'none';
            } else if (data.status === 'red') {
                modalTitle.textContent = '🚨 ATENÇÃO - Paciente Instável';
                modalMessage.textContent = 'RISCO ELEVADO: O paciente está instável. Isso pode comprometer a qualidade do exame.';
                modalConfirm.style.display = 'none';
                modalForce.style.display = 'inline-block';
            }
            
            modal.style.display = 'block';
        }
        
        function closeModal() {
            modal.style.display = 'none';
        }
        
        function confirmStart() {
            closeModal();
            forceStart();
        }
        
        function forceStart() {
            closeModal();
            fetch('/start_procedure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ force_start: true })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    activateProcedure();
                } else {
                    alert('Erro: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao comunicar com servidor');
            });
        }
        
        // Fecha modal ao clicar fora
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal();
            }
        });
        
        // 🔄 ATUALIZAÇÃO DE STATUS EM TEMPO REAL
        function updateSystemStatus() {
            fetch('/get_status')
                .then(response => response.json())
                .then(data => {
                    // Atualiza indicadores de estabilidade
                    updateStabilityIndicators(data.stability_level);
                    
                    // Atualiza timer se procedimento ativo
                    if (data.procedure_active && !procedureActive) {
                        // Procedimento foi iniciado externamente
                        activateProcedure();
                    } else if (!data.procedure_active && procedureActive) {
                        // Procedimento foi parado externamente
                        deactivateProcedure("Finalizado");
                    }
                })
                .catch(error => {
                    console.log('Status update error:', error);
                });
        }
        
        function updateStabilityIndicators(level) {
            // Reseta todas as indicações
            const indicators = document.querySelectorAll('.stability-level');
            indicators.forEach(indicator => {
                indicator.style.opacity = '0.3';
                indicator.style.fontWeight = 'normal';
            });
            
            // Destaca o nível atual
            if (level === 'green') {
                const greenIndicator = document.querySelector('.level-green');
                greenIndicator.style.opacity = '1';
                greenIndicator.style.fontWeight = 'bold';
                greenIndicator.style.boxShadow = '0 0 10px #28a745';
            } else if (level === 'yellow') {
                const yellowIndicator = document.querySelector('.level-yellow');
                yellowIndicator.style.opacity = '1';
                yellowIndicator.style.fontWeight = 'bold';
                yellowIndicator.style.boxShadow = '0 0 10px #ffc107';
            } else if (level === 'red') {
                const redIndicator = document.querySelector('.level-red');
                redIndicator.style.opacity = '1';
                redIndicator.style.fontWeight = 'bold';
                redIndicator.style.boxShadow = '0 0 10px #dc3545';
            }
        }
        
        // Inicia monitoramento de status a cada 1 segundo
        setInterval(updateSystemStatus, 1000);
        
        console.log('✅ Sistema Médico Profissional carregado com sucesso!');
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 50)
    print("🏥 SISTEMA MÉDICO PROFISSIONAL v2.0")
    print("   Monitoramento de Estabilidade da Cabeça")
    print("=" * 50)
    
    # Inicialização dos sistemas
    init_tts()
    init_camera()
    init_analyzer()
    
    print("\n🏥 Sistema Médico de Estabilidade da Cabeça")
    print("🌐 Acesse: http://127.0.0.1:5000")
    print("📋 Procedimentos suportados:")
    print("   • Ressonância Magnética do Crânio")
    print("   • Tomografia Computadorizada da Cabeça") 
    print("   • Radiografia da Cabeça (Raio-X)")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Sistema finalizado pelo usuário")
    finally:
        if camera:
            camera.release()
        cv2.destroyAllWindows()
