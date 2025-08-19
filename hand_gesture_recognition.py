import cv2
import numpy as np
import math
from collections import deque

class HandGestureRecognizer:
    def __init__(self):
        # Histórico para análise temporal
        self.hand_history = deque(maxlen=20)
        self.gesture_cooldown = {}
        self.frame_count = 0
        
        # Configurações de detecção de mãos
        self.hand_detector = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        # Parâmetros de detecção
        self.min_hand_area = 1000
        self.max_hand_area = 50000
        self.gesture_stability = 8
        
    def detect_hands_by_skin(self, frame):
        """Detecta mãos usando detecção de cor de pele"""
        # Converte para HSV para melhor detecção de pele
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Definir ranges de cor de pele em HSV
        lower_skin1 = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin1 = np.array([20, 255, 255], dtype=np.uint8)
        
        lower_skin2 = np.array([170, 20, 70], dtype=np.uint8)
        upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
        
        # Criar máscaras
        mask1 = cv2.inRange(hsv, lower_skin1, upper_skin1)
        mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Aplicar filtros morfológicos
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)
        
        # Aplicar filtro Gaussiano
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    def detect_hands_by_motion(self, frame):
        """Detecta mãos usando detecção de movimento"""
        # Aplica subtração de fundo
        fg_mask = self.hand_detector.apply(frame)
        
        # Filtros morfológicos
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, self.kernel)
        
        return fg_mask
    
    def find_hand_contours(self, frame):
        """Encontra contornos das mãos"""
        # Combina detecção por pele e movimento
        skin_mask = self.detect_hands_by_skin(frame)
        motion_mask = self.detect_hands_by_motion(frame)
        
        # Combina as duas máscaras
        combined_mask = cv2.bitwise_and(skin_mask, motion_mask)
        
        # Encontra contornos
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtra contornos por área
        hand_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_hand_area < area < self.max_hand_area:
                # Aproxima contorno para reduzir ruído
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                hand_contours.append(contour)
        
        return hand_contours, combined_mask
    
    def analyze_hand_shape(self, contour):
        """Analisa a forma da mão para detectar gestos"""
        if len(contour) < 5:
            return None
            
        # Calcula hull convexo
        hull = cv2.convexHull(contour, returnPoints=False)
        
        # Encontra defeitos de convexidade (dedos)
        if len(hull) > 3:
            defects = cv2.convexityDefects(contour, hull)
            
            if defects is not None:
                finger_count = self.count_fingers(contour, defects)
                return self.classify_gesture_by_fingers(finger_count)
        
        return None
    
    def count_fingers(self, contour, defects):
        """Conta dedos baseado em defeitos de convexidade"""
        finger_count = 0
        
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = tuple(contour[s][0])
            end = tuple(contour[e][0])
            far = tuple(contour[f][0])
            
            # Calcula ângulo entre dedos
            a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
            c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
            
            # Calcula ângulo usando lei dos cossenos
            if a > 0 and b > 0 and c > 0:
                angle = math.acos((b**2 + c**2 - a**2) / (2 * b * c)) * 180 / math.pi
                
                # Se ângulo for menor que 90 graus, considera como dedo
                if angle <= 90:
                    finger_count += 1
        
        return finger_count
    
    def classify_gesture_by_fingers(self, finger_count):
        """Classifica gesto baseado no número de dedos"""
        gestures = {
            0: "punho fechado",
            1: "apontando",
            2: "sinal de paz",
            3: "três dedos", 
            4: "quatro dedos",
            5: "mão aberta"
        }
        
        return gestures.get(finger_count, "gesto desconhecido")
    
    def detect_wave_motion(self, hand_centers):
        """Detecta movimento de acenar baseado no centro das mãos"""
        if len(hand_centers) < 10:
            return False
        
        # Analisa movimento horizontal
        x_positions = [center[0] for center in hand_centers[-10:]]
        x_variation = max(x_positions) - min(x_positions)
        
        # Calcula velocidade média
        velocities = []
        for i in range(1, len(hand_centers)):
            prev_center = hand_centers[i-1]
            curr_center = hand_centers[i]
            velocity = math.sqrt((curr_center[0] - prev_center[0])**2 + 
                               (curr_center[1] - prev_center[1])**2)
            velocities.append(velocity)
        
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0
        
        # Acenar = grande variação horizontal + velocidade adequada
        return x_variation > 60 and avg_velocity > 8
    
    def detect_clap_motion(self, hand_contours):
        """Detecta bater palmas baseado na proximidade de duas mãos"""
        if len(hand_contours) < 2:
            return False
        
        # Calcula centros das duas maiores mãos
        sorted_contours = sorted(hand_contours, key=cv2.contourArea, reverse=True)[:2]
        
        centers = []
        for contour in sorted_contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centers.append((cx, cy))
        
        if len(centers) == 2:
            distance = math.sqrt((centers[0][0] - centers[1][0])**2 + 
                               (centers[0][1] - centers[1][1])**2)
            
            # Se as mãos estão muito próximas, pode ser palma
            return distance < 100
        
        return False
    
    def process_frame(self, frame):
        """Processa frame e detecta gestos de mão"""
        self.frame_count += 1
        
        # Encontra contornos das mãos
        hand_contours, mask = self.find_hand_contours(frame)
        
        detected_gestures = []
        hand_centers = []
        
        # Processa cada mão detectada
        for i, contour in enumerate(hand_contours):
            # Calcula centro da mão
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                hand_centers.append((cx, cy))
                
                # Desenha contorno da mão em destaque
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 3)
                
                # Desenha círculo no centro da mão
                cv2.circle(frame, (cx, cy), 10, (255, 0, 0), -1)
                
                # Desenha retângulo ao redor da mão
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
                
                # Analisa forma da mão
                gesture = self.analyze_hand_shape(contour)
                if gesture:
                    detected_gestures.append(gesture)
                    # Mostra gesto detectado
                    cv2.putText(frame, f"Mao {i+1}: {gesture}", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Adiciona centros ao histórico
        if hand_centers:
            self.hand_history.extend(hand_centers)
        
        # Detecta gestos de movimento
        if self.detect_wave_motion(list(self.hand_history)):
            if not self._check_cooldown("acenar"):
                detected_gestures.append("acenando")
                self._set_cooldown("acenar")
        
        if self.detect_clap_motion(hand_contours):
            if not self._check_cooldown("batendo_palmas"):
                detected_gestures.append("batendo palmas")
                self._set_cooldown("batendo_palmas")
        
        # Mostra informações na tela
        cv2.putText(frame, f"Maos detectadas: {len(hand_contours)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostra máscara de detecção (opcional)
        if len(hand_contours) > 0:
            mask_colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
            frame[0:mask.shape[0]//4, 0:mask.shape[1]//4] = cv2.resize(mask_colored, 
                                                                      (mask.shape[1]//4, mask.shape[0]//4))
        
        return frame, detected_gestures
    
    def _check_cooldown(self, gesture_name, cooldown_frames=30):
        """Verifica cooldown do gesto"""
        if gesture_name in self.gesture_cooldown:
            return self.frame_count - self.gesture_cooldown[gesture_name] < cooldown_frames
        return False
    
    def _set_cooldown(self, gesture_name):
        """Define cooldown do gesto"""
        self.gesture_cooldown[gesture_name] = self.frame_count
