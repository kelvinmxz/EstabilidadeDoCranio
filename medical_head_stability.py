import cv2
import numpy as np
from collections import deque
import time
import math

class MedicalHeadStabilityAnalyzer:
    """
    Sistema Médico de Análise de Estabilidade da Cabeça
    
    Desenvolvido para procedimentos de imagem médica que exigem estabilidade:
    - Ressonância Magnética do Crânio
    - Tomografia Computadorizada da Cabeça  
    - Radiografia da Cabeça (Raio-X)
    """
    
    def __init__(self, stability_threshold=10, time_threshold=3.0, sensitivity='medium'):
        # Configurações de estabilidade
        self.stability_threshold = stability_threshold  # Pixels de movimento máximo
        self.time_threshold = time_threshold  # Tempo necessário de estabilidade (segundos)
        
        # Configurações de sensibilidade
        sensitivity_config = {
            'high': {'threshold': 5, 'min_detections': 20},
            'medium': {'threshold': 10, 'min_detections': 15}, 
            'low': {'threshold': 20, 'min_detections': 10}
        }
        
        config = sensitivity_config.get(sensitivity, sensitivity_config['medium'])
        self.stability_threshold = config['threshold']
        self.min_detections = config['min_detections']
        
        # Detectores
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Histórico de posições
        self.position_history = deque(maxlen=30)  # 30 frames de histórico
        self.stability_history = deque(maxlen=100)  # Histórico de estabilidade
        
        # Controle temporal
        self.stable_start_time = None
        self.last_detection_time = time.time()
        
        # Status do sistema
        self.is_stable = False
        self.is_ready_for_procedure = False
        self.stability_score = 0.0
        self.message = "Aguardando detecção..."
        
        # Estatísticas
        self.total_frames = 0
        self.stable_frames = 0
        self.max_movement = 0
        
    def detect_head_position(self, frame):
        """Detecta a posição da cabeça no frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(50, 50)
        )
        
        if len(faces) > 0:
            # Pega o maior rosto detectado
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            
            # Centro da cabeça
            center_x = x + w // 2
            center_y = y + h // 2
            
            return (center_x, center_y, w, h), faces
        
        return None, faces
    
    def calculate_movement(self, current_pos, previous_pos):
        """Calcula o movimento entre duas posições"""
        if current_pos is None or previous_pos is None:
            return float('inf')
        
        dx = current_pos[0] - previous_pos[0]
        dy = current_pos[1] - previous_pos[1]
        return math.sqrt(dx*dx + dy*dy)
    
    def analyze_stability(self, frame):
        """Analisa a estabilidade da cabeça"""
        self.total_frames += 1
        current_time = time.time()
        
        # Detecta posição da cabeça
        head_pos, all_faces = self.detect_head_position(frame)
        
        if head_pos is None:
            self.message = "❌ Cabeça não detectada - Posicione-se na frente da câmera"
            self.is_stable = False
            self.is_ready_for_procedure = False
            self.stability_score = 0.0
            self.stable_start_time = None
            return False
        
        # Adiciona posição atual ao histórico
        self.position_history.append(head_pos)
        self.last_detection_time = current_time
        
        # Verifica se tem histórico suficiente
        if len(self.position_history) < 2:
            self.message = "📊 Coletando dados de posição..."
            return False
        
        # Calcula movimento
        movement = self.calculate_movement(head_pos, self.position_history[-2])
        self.max_movement = max(self.max_movement, movement)
        
        # Verifica estabilidade
        is_currently_stable = movement <= self.stability_threshold
        self.stability_history.append(is_currently_stable)
        
        if is_currently_stable:
            self.stable_frames += 1
            
            if self.stable_start_time is None:
                self.stable_start_time = current_time
            
            # Tempo estável
            stable_duration = current_time - self.stable_start_time
            
            # Calcula score de estabilidade (baseado em últimos frames)
            recent_stability = list(self.stability_history)[-self.min_detections:]
            if len(recent_stability) >= self.min_detections:
                self.stability_score = sum(recent_stability) / len(recent_stability) * 100
            else:
                self.stability_score = 0
            
            # Verifica se está pronto para procedimento
            if stable_duration >= self.time_threshold and self.stability_score >= 80:
                self.is_ready_for_procedure = True
                self.message = f"✅ PRONTO PARA PROCEDIMENTO ({stable_duration:.1f}s estável)"
            else:
                remaining_time = max(0, self.time_threshold - stable_duration)
                self.message = f"⏳ Mantendo posição... {remaining_time:.1f}s restantes"
            
            self.is_stable = True
            
        else:
            # Não está estável
            self.stable_start_time = None
            self.is_stable = False
            self.is_ready_for_procedure = False
            self.stability_score = max(0, self.stability_score - 10)  # Decrementa score
            self.message = f"⚠️ Movimento detectado ({movement:.1f}px) - Mantenha a cabeça imóvel"
        
        return self.is_ready_for_procedure
    
    def draw_stability_info(self, frame):
        """Desenha informações de estabilidade no frame"""
        height, width = frame.shape[:2]
        
        # Detecta posição atual
        head_pos, all_faces = self.detect_head_position(frame)
        
        if head_pos:
            x, y, w, h = head_pos
            
            # Cor baseada na estabilidade
            if self.is_ready_for_procedure:
                color = (0, 255, 0)  # Verde - Pronto
                thickness = 4
            elif self.is_stable:
                color = (0, 255, 255)  # Amarelo - Estável mas não pronto
                thickness = 3
            else:
                color = (0, 0, 255)  # Vermelho - Instável
                thickness = 2
            
            # Desenha retângulo da cabeça
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)
            
            # Desenha ponto central
            center_x, center_y = x + w//2, y + h//2
            cv2.circle(frame, (center_x, center_y), 5, color, -1)
            
            # Desenha cruz de referência
            cv2.line(frame, (center_x-10, center_y), (center_x+10, center_y), color, 2)
            cv2.line(frame, (center_x, center_y-10), (center_x, center_y+10), color, 2)
            
            # Status sobre a cabeça
            status_text = "PRONTO" if self.is_ready_for_procedure else "ESTÁVEL" if self.is_stable else "INSTÁVEL"
            cv2.putText(frame, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Painel de informações
        self._draw_info_panel(frame)
        
        # Indicador visual de status
        self._draw_status_indicator(frame)
        
        return frame
    
    def _draw_info_panel(self, frame):
        """Desenha painel com informações detalhadas"""
        height, width = frame.shape[:2]
        
        # Fundo semi-transparente
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (width-10, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Título
        cv2.putText(frame, "SISTEMA MEDICO DE ESTABILIDADE", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Informações
        info_lines = [
            f"Status: {self.message}",
            f"Estabilidade: {self.stability_score:.1f}%",
            f"Threshold: {self.stability_threshold}px",
            f"Tempo necessario: {self.time_threshold}s",
            f"Frames processados: {self.total_frames}",
            f"Frames estaveis: {self.stable_frames}"
        ]
        
        y_pos = 60
        for line in info_lines:
            color = (255, 255, 255)
            if "Status:" in line:
                if "PRONTO" in line:
                    color = (0, 255, 0)
                elif "Movimento" in line:
                    color = (0, 0, 255)
                elif "Mantendo" in line:
                    color = (0, 255, 255)
            
            cv2.putText(frame, line, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_pos += 20
    
    def _draw_status_indicator(self, frame):
        """Desenha indicador visual grande de status"""
        height, width = frame.shape[:2]
        
        # Posição do indicador (canto superior direito)
        indicator_x = width - 150
        indicator_y = 50
        indicator_size = 40
        
        if self.is_ready_for_procedure:
            # Verde - Pronto para procedimento
            cv2.circle(frame, (indicator_x, indicator_y), indicator_size, (0, 255, 0), -1)
            cv2.putText(frame, "GO", (indicator_x-15, indicator_y+5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Texto grande
            cv2.putText(frame, "INICIAR PROCEDIMENTO", (indicator_x-100, indicator_y+60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
        elif self.is_stable:
            # Amarelo - Estável mas aguardando
            cv2.circle(frame, (indicator_x, indicator_y), indicator_size, (0, 255, 255), -1)
            cv2.putText(frame, "WAIT", (indicator_x-20, indicator_y+5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        else:
            # Vermelho - Não estável
            cv2.circle(frame, (indicator_x, indicator_y), indicator_size, (0, 0, 255), -1)
            cv2.putText(frame, "STOP", (indicator_x-20, indicator_y+5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def get_stability_report(self):
        """Retorna relatório detalhado de estabilidade"""
        stability_percentage = (self.stable_frames / max(1, self.total_frames)) * 100
        
        return {
            'is_ready': self.is_ready_for_procedure,
            'is_stable': self.is_stable,
            'stability_score': self.stability_score,
            'stability_percentage': stability_percentage,
            'total_frames': self.total_frames,
            'stable_frames': self.stable_frames,
            'max_movement': self.max_movement,
            'message': self.message,
            'threshold': self.stability_threshold,
            'time_threshold': self.time_threshold
        }
    
    def reset_analysis(self):
        """Reinicia a análise"""
        self.position_history.clear()
        self.stability_history.clear()
        self.stable_start_time = None
        self.is_stable = False
        self.is_ready_for_procedure = False
        self.stability_score = 0.0
        self.total_frames = 0
        self.stable_frames = 0
        self.max_movement = 0
        self.message = "Sistema reiniciado - Aguardando detecção..."
