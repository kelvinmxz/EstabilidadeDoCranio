import cv2
import numpy as np
from collections import deque
import os

class FacePartDetector:
    def __init__(self):
        # Carrega os classificadores Haar Cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        
        # Histórico para análise
        self.detection_history = deque(maxlen=10)
        self.frame_count = 0
        
        # Cores para cada parte do rosto
        self.colors = {
            'face': (255, 0, 0),      # Azul para rosto
            'left_eye': (0, 255, 0),  # Verde para olho esquerdo
            'right_eye': (0, 255, 255), # Amarelo para olho direito
            'mouth': (255, 0, 255),   # Magenta para boca
            'nose': (0, 255, 255),    # Ciano para nariz
            'smile': (128, 0, 128)    # Roxo para sorriso
        }
        
        # Expressões detectadas
        self.current_expressions = []
        
    def detect_face_parts(self, frame):
        """Detecta partes do rosto"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.frame_count += 1
        
        # Detecta rostos
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        detected_parts = []
        self.current_expressions.clear()
        
        for (x, y, w, h) in faces:
            # Desenha retângulo do rosto
            cv2.rectangle(frame, (x, y), (x+w, y+h), self.colors['face'], 3)
            cv2.putText(frame, 'ROSTO', (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['face'], 2)
            
            detected_parts.append('rosto')
            
            # Região do rosto para detectar outras partes
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            
            # Detecta olhos
            eyes = self.eye_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(15, 15)
            )
            
            eye_count = 0
            for (ex, ey, ew, eh) in eyes:
                eye_count += 1
                eye_label = 'OLHO ESQUERDO' if eye_count == 1 else 'OLHO DIREITO'
                eye_color = self.colors['left_eye'] if eye_count == 1 else self.colors['right_eye']
                
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), eye_color, 2)
                cv2.putText(roi_color, eye_label, (ex, ey-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, eye_color, 1)
                
                # Desenha círculo no centro do olho
                eye_center = (ex + ew//2, ey + eh//2)
                cv2.circle(roi_color, eye_center, 3, eye_color, -1)
                
                detected_parts.append(f'olho_{eye_count}')
                
                if eye_count >= 2:  # Limita a 2 olhos
                    break
            
            # Detecta sorriso/boca
            smiles = self.smile_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.8,
                minNeighbors=20,
                minSize=(25, 25)
            )
            
            for (sx, sy, sw, sh) in smiles:
                cv2.rectangle(roi_color, (sx, sy), (sx+sw, sy+sh), self.colors['smile'], 2)
                cv2.putText(roi_color, 'SORRINDO', (sx, sy-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['smile'], 1)
                detected_parts.append('sorriso')
                self.current_expressions.append('sorrindo')
                break
            
            # Estima posição do nariz (região central do rosto)
            nose_x = w // 2 - 15
            nose_y = int(h * 0.4)
            nose_w = 30
            nose_h = 25
            
            if nose_x > 0 and nose_y > 0:
                cv2.rectangle(roi_color, (nose_x, nose_y), 
                             (nose_x + nose_w, nose_y + nose_h), 
                             self.colors['nose'], 2)
                cv2.putText(roi_color, 'NARIZ', (nose_x, nose_y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['nose'], 1)
                detected_parts.append('nariz')
            
            # Estima posição da boca (se não há sorriso)
            if 'sorriso' not in detected_parts:
                mouth_x = w // 2 - 20
                mouth_y = int(h * 0.7)
                mouth_w = 40
                mouth_h = 20
                
                if mouth_x > 0 and mouth_y > 0:
                    cv2.rectangle(roi_color, (mouth_x, mouth_y), 
                                 (mouth_x + mouth_w, mouth_y + mouth_h), 
                                 self.colors['mouth'], 2)
                    cv2.putText(roi_color, 'BOCA', (mouth_x, mouth_y-5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['mouth'], 1)
                    detected_parts.append('boca')
            
            # Detecta sobrancelhas (estimativa)
            eyebrow_y = int(h * 0.25)
            eyebrow_h = 10
            
            # Sobrancelha esquerda
            left_eyebrow_x = int(w * 0.2)
            left_eyebrow_w = int(w * 0.25)
            cv2.rectangle(roi_color, (left_eyebrow_x, eyebrow_y), 
                         (left_eyebrow_x + left_eyebrow_w, eyebrow_y + eyebrow_h), 
                         (0, 128, 255), 1)
            cv2.putText(roi_color, 'SOBRANCELHA E', (left_eyebrow_x, eyebrow_y-3),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 128, 255), 1)
            
            # Sobrancelha direita
            right_eyebrow_x = int(w * 0.55)
            right_eyebrow_w = int(w * 0.25)
            cv2.rectangle(roi_color, (right_eyebrow_x, eyebrow_y), 
                         (right_eyebrow_x + right_eyebrow_w, eyebrow_y + eyebrow_h), 
                         (255, 128, 0), 1)
            cv2.putText(roi_color, 'SOBRANCELHA D', (right_eyebrow_x, eyebrow_y-3),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 128, 0), 1)
            
            detected_parts.extend(['sobrancelha_esquerda', 'sobrancelha_direita'])
        
        # Adiciona ao histórico
        self.detection_history.append({
            'frame': self.frame_count,
            'parts': detected_parts,
            'expressions': self.current_expressions.copy()
        })
        
        return detected_parts, self.current_expressions
    
    def analyze_expressions(self):
        """Analisa expressões faciais baseado no histórico"""
        if len(self.detection_history) < 5:
            return []
        
        recent_expressions = []
        for record in list(self.detection_history)[-5:]:
            recent_expressions.extend(record['expressions'])
        
        # Conta expressões consistentes
        expression_counts = {}
        for expr in recent_expressions:
            expression_counts[expr] = expression_counts.get(expr, 0) + 1
        
        # Retorna expressões que aparecem em pelo menos 3 dos últimos 5 frames
        consistent_expressions = [expr for expr, count in expression_counts.items() if count >= 3]
        
        return consistent_expressions
    
    def get_face_info(self):
        """Retorna informações sobre as partes detectadas"""
        if not self.detection_history:
            return {"parts": [], "expressions": [], "count": 0}
        
        latest = self.detection_history[-1]
        consistent_expressions = self.analyze_expressions()
        
        # Traduz partes para português
        part_translations = {
            'rosto': 'rosto',
            'olho_1': 'olho esquerdo',
            'olho_2': 'olho direito', 
            'nariz': 'nariz',
            'boca': 'boca',
            'sorriso': 'sorriso',
            'sobrancelha_esquerda': 'sobrancelha esquerda',
            'sobrancelha_direita': 'sobrancelha direita'
        }
        
        translated_parts = [part_translations.get(part, part) for part in latest['parts']]
        
        return {
            "parts": translated_parts,
            "expressions": consistent_expressions,
            "count": len([p for p in latest['parts'] if 'rosto' in p])
        }
    
    def draw_info_overlay(self, frame):
        """Desenha informações na tela"""
        info = self.get_face_info()
        
        y_offset = 30
        
        # Título
        cv2.putText(frame, f"PARTES DO ROSTO DETECTADAS:", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_offset += 30
        
        # Lista partes detectadas
        if info['parts']:
            for i, part in enumerate(info['parts']):
                color = (0, 255, 0) if i < 8 else (255, 255, 0)
                cv2.putText(frame, f"• {part.upper()}", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                y_offset += 25
        else:
            cv2.putText(frame, "• Nenhuma parte detectada", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            y_offset += 25
        
        # Expressões
        if info['expressions']:
            cv2.putText(frame, f"EXPRESSAO: {', '.join(info['expressions']).upper()}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        
        return frame
