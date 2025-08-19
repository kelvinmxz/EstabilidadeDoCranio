import numpy as np
import cv2
from collections import deque
import math

class GestureRecognizer:
    def __init__(self):
        # Histórico de poses para análise temporal
        self.pose_history = deque(maxlen=30)  # 30 frames de histórico
        self.hand_positions = deque(maxlen=20)
        self.gesture_cooldown = {}
        self.frame_count = 0
        
        # Parâmetros de detecção
        self.min_confidence = 0.6
        self.wave_threshold = 40  # Movimento mínimo para acenar
        self.clap_distance_threshold = 80  # Distância máxima entre mãos para palmas
        self.gesture_stability = 5  # Frames mínimos para confirmar gesto
        
    def add_pose(self, keypoints):
        """Adiciona nova pose ao histórico"""
        if keypoints is None or len(keypoints) == 0:
            return
            
        self.frame_count += 1
        pose_data = self._extract_pose_features(keypoints)
        if pose_data:
            self.pose_history.append(pose_data)
            
    def _extract_pose_features(self, keypoints):
        """Extrai características importantes da pose"""
        try:
            kpts = keypoints[0]  # Primeira pessoa
            if len(kpts) < 17:
                return None
                
            # Pontos importantes com confiança
            features = {
                'frame': self.frame_count,
                'nose': kpts[0] if kpts[0][2] > self.min_confidence else None,
                'left_shoulder': kpts[5] if kpts[5][2] > self.min_confidence else None,
                'right_shoulder': kpts[6] if kpts[6][2] > self.min_confidence else None,
                'left_elbow': kpts[7] if kpts[7][2] > self.min_confidence else None,
                'right_elbow': kpts[8] if kpts[8][2] > self.min_confidence else None,
                'left_wrist': kpts[9] if kpts[9][2] > self.min_confidence else None,
                'right_wrist': kpts[10] if kpts[10][2] > self.min_confidence else None,
            }
            
            return features
            
        except Exception as e:
            print(f"Erro ao extrair features: {e}")
            return None
    
    def _check_cooldown(self, gesture_name, cooldown_frames=15):
        """Verifica se o gesto está em cooldown"""
        if gesture_name in self.gesture_cooldown:
            if self.frame_count - self.gesture_cooldown[gesture_name] < cooldown_frames:
                return True
        return False
    
    def _set_cooldown(self, gesture_name):
        """Define cooldown para um gesto"""
        self.gesture_cooldown[gesture_name] = self.frame_count
    
    def detect_waving(self):
        """Detecta movimento de acenar"""
        if len(self.pose_history) < 10:
            return False
            
        if self._check_cooldown("acenar"):
            return False
            
        try:
            # Analisa movimento das mãos nos últimos frames
            recent_poses = list(self.pose_history)[-10:]
            
            # Verifica mão direita
            right_wave = self._detect_hand_wave(recent_poses, 'right_wrist')
            left_wave = self._detect_hand_wave(recent_poses, 'left_wrist')
            
            if right_wave or left_wave:
                self._set_cooldown("acenar")
                return True
                
        except Exception as e:
            print(f"Erro ao detectar acenar: {e}")
            
        return False
    
    def _detect_hand_wave(self, poses, hand_key):
        """Detecta movimento de acenar de uma mão específica"""
        valid_positions = []
        
        for pose in poses:
            if pose[hand_key] is not None:
                valid_positions.append((pose[hand_key][0], pose[hand_key][1]))
        
        if len(valid_positions) < 6:
            return False
            
        # Calcula variação horizontal (movimento de acenar)
        x_positions = [pos[0] for pos in valid_positions]
        x_variation = max(x_positions) - min(x_positions)
        
        # Calcula a velocidade do movimento
        velocities = []
        for i in range(1, len(valid_positions)):
            dx = valid_positions[i][0] - valid_positions[i-1][0]
            dy = valid_positions[i][1] - valid_positions[i-1][1]
            speed = math.sqrt(dx*dx + dy*dy)
            velocities.append(speed)
        
        avg_speed = sum(velocities) / len(velocities) if velocities else 0
        
        # Acenar = movimento horizontal significativo + velocidade adequada
        return x_variation > self.wave_threshold and avg_speed > 5
    
    def detect_clapping(self):
        """Detecta bater palmas"""
        if len(self.pose_history) < 5:
            return False
            
        if self._check_cooldown("bater_palmas"):
            return False
            
        try:
            current_pose = self.pose_history[-1]
            
            if (current_pose['left_wrist'] is None or 
                current_pose['right_wrist'] is None):
                return False
            
            # Calcula distância entre as mãos
            left_hand = current_pose['left_wrist']
            right_hand = current_pose['right_wrist']
            
            distance = math.sqrt(
                (left_hand[0] - right_hand[0])**2 + 
                (left_hand[1] - right_hand[1])**2
            )
            
            # Verifica se as mãos estão próximas (possível palma)
            if distance < self.clap_distance_threshold:
                # Verifica movimento recente (se as mãos se aproximaram rapidamente)
                if len(self.pose_history) >= 3:
                    prev_poses = list(self.pose_history)[-3:-1]
                    prev_distances = []
                    
                    for pose in prev_poses:
                        if (pose['left_wrist'] is not None and 
                            pose['right_wrist'] is not None):
                            prev_dist = math.sqrt(
                                (pose['left_wrist'][0] - pose['right_wrist'][0])**2 + 
                                (pose['left_wrist'][1] - pose['right_wrist'][1])**2
                            )
                            prev_distances.append(prev_dist)
                    
                    # Se as mãos estavam mais distantes antes, é uma palma
                    if prev_distances and min(prev_distances) > distance + 20:
                        self._set_cooldown("bater_palmas")
                        return True
                        
        except Exception as e:
            print(f"Erro ao detectar palmas: {e}")
            
        return False
    
    def detect_pointing(self):
        """Detecta apontar melhorado"""
        if len(self.pose_history) < 3:
            return False
            
        if self._check_cooldown("apontar"):
            return False
            
        try:
            current_pose = self.pose_history[-1]
            
            # Verifica braço direito estendido
            right_pointing = self._detect_arm_pointing(current_pose, 'right')
            left_pointing = self._detect_arm_pointing(current_pose, 'left')
            
            if right_pointing or left_pointing:
                self._set_cooldown("apontar")
                return True
                
        except Exception as e:
            print(f"Erro ao detectar apontar: {e}")
            
        return False
    
    def _detect_arm_pointing(self, pose, side):
        """Detecta se um braço está apontando"""
        shoulder_key = f'{side}_shoulder'
        elbow_key = f'{side}_elbow'
        wrist_key = f'{side}_wrist'
        
        if (pose[shoulder_key] is None or 
            pose[elbow_key] is None or 
            pose[wrist_key] is None):
            return False
        
        shoulder = pose[shoulder_key]
        elbow = pose[elbow_key]
        wrist = pose[wrist_key]
        
        # Calcula ângulos do braço
        shoulder_to_elbow = math.sqrt(
            (elbow[0] - shoulder[0])**2 + (elbow[1] - shoulder[1])**2
        )
        elbow_to_wrist = math.sqrt(
            (wrist[0] - elbow[0])**2 + (wrist[1] - elbow[1])**2
        )
        
        if shoulder_to_elbow == 0 or elbow_to_wrist == 0:
            return False
        
        # Calcula se o braço está estendido
        arm_extension_ratio = elbow_to_wrist / shoulder_to_elbow
        
        # Verifica se o braço está horizontal (apontando)
        arm_angle = math.atan2(wrist[1] - shoulder[1], wrist[0] - shoulder[0])
        arm_angle_degrees = abs(math.degrees(arm_angle))
        
        # Apontando = braço estendido + aproximadamente horizontal
        is_extended = arm_extension_ratio > 0.7
        is_horizontal = 160 <= arm_angle_degrees <= 200 or arm_angle_degrees <= 20
        
        return is_extended and is_horizontal
    
    def detect_thumbs_up(self):
        """Detecta joia (polegar para cima) - aproximação"""
        if len(self.pose_history) < 3:
            return False
            
        if self._check_cooldown("joia"):
            return False
            
        try:
            current_pose = self.pose_history[-1]
            
            # Aproximação: mão levantada próxima ao ombro
            if (current_pose['right_wrist'] is not None and 
                current_pose['right_shoulder'] is not None):
                
                wrist = current_pose['right_wrist']
                shoulder = current_pose['right_shoulder']
                
                # Mão acima do ombro e próxima lateralmente
                if (wrist[1] < shoulder[1] - 30 and 
                    abs(wrist[0] - shoulder[0]) < 100):
                    self._set_cooldown("joia")
                    return True
                    
        except Exception as e:
            print(f"Erro ao detectar joia: {e}")
            
        return False
    
    def detect_peace_sign(self):
        """Detecta sinal de paz - aproximação"""
        if len(self.pose_history) < 3:
            return False
            
        if self._check_cooldown("paz"):
            return False
            
        try:
            current_pose = self.pose_history[-1]
            
            # Aproximação: mão levantada próxima à cabeça
            if (current_pose['right_wrist'] is not None and 
                current_pose['nose'] is not None):
                
                wrist = current_pose['right_wrist']
                nose = current_pose['nose']
                
                # Mão próxima à cabeça
                distance_to_head = math.sqrt(
                    (wrist[0] - nose[0])**2 + (wrist[1] - nose[1])**2
                )
                
                if distance_to_head < 150 and wrist[1] < nose[1]:
                    self._set_cooldown("paz")
                    return True
                    
        except Exception as e:
            print(f"Erro ao detectar paz: {e}")
            
        return False
    
    def get_all_gestures(self):
        """Retorna todos os gestos detectados no frame atual"""
        gestures = []
        
        if self.detect_waving():
            gestures.append("acenando")
            
        if self.detect_clapping():
            gestures.append("batendo palmas")
            
        if self.detect_pointing():
            gestures.append("apontando")
            
        if self.detect_thumbs_up():
            gestures.append("fazendo joia")
            
        if self.detect_peace_sign():
            gestures.append("fazendo sinal de paz")
            
        return gestures
