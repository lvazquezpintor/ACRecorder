"""
Detector de Curvas - Analiza el ángulo del volante para detectar y contar curvas

Uso en tiempo real:
    detector = CurveDetector()
    stats = detector.update(steer_angle, timestamp)
    
Uso para análisis post-sesión:
    results = analyze_telemetry_curves(telemetry_data)
"""

from typing import List, Dict, Optional
from collections import deque

class CurveDetector:
    """
    Detecta curvas basándose en el ángulo del volante (steer_angle)
    """
    
    def __init__(self, 
                 threshold_angle: float = 15.0,     # Ángulo mínimo para considerar una curva
                 min_duration: int = 2,             # Mínimo de muestras para ser una curva
                 cooldown_samples: int = 3):        # Muestras de espera antes de detectar otra curva
        """
        Args:
            threshold_angle: Ángulo absoluto mínimo del volante para considerar curva (grados)
            min_duration: Número mínimo de muestras consecutivas en curva
            cooldown_samples: Muestras de "recta" necesarias antes de detectar nueva curva
        """
        self.threshold_angle = threshold_angle
        self.min_duration = min_duration
        self.cooldown_samples = cooldown_samples
        
        # Estado interno
        self.history = deque(maxlen=10)  # Últimos 10 ángulos
        self.in_curve = False
        self.curve_samples = 0
        self.cooldown_counter = 0
        self.current_curve_direction = None  # 'left', 'right', None
        
        # Estadísticas
        self.total_curves = 0
        self.left_curves = 0
        self.right_curves = 0
        self.curves_log = []  # Lista de curvas detectadas
        
    def update(self, steer_angle: float, timestamp: str = None) -> Dict:
        """
        Actualiza el detector con un nuevo ángulo del volante
        
        Args:
            steer_angle: Ángulo del volante en grados (+ = derecha, - = izquierda)
            timestamp: Timestamp opcional del sample
            
        Returns:
            Diccionario con información de detección de curva
        """
        self.history.append(steer_angle)
        abs_angle = abs(steer_angle)
        
        # Determinar dirección actual
        if steer_angle > self.threshold_angle:
            current_direction = 'right'
        elif steer_angle < -self.threshold_angle:
            current_direction = 'left'
        else:
            current_direction = None
        
        curve_detected = False
        curve_finished = False
        
        # Lógica de detección
        if current_direction is not None:  # Estamos girando
            self.cooldown_counter = 0
            
            if not self.in_curve:  # Iniciando una curva
                self.in_curve = True
                self.curve_samples = 1
                self.current_curve_direction = current_direction
            else:  # Ya en curva
                # Verificar si cambió de dirección (curva en S)
                if current_direction != self.current_curve_direction:
                    # Terminar curva anterior si cumple duración mínima
                    if self.curve_samples >= self.min_duration:
                        curve_finished = True
                        self._register_curve(timestamp)
                    # Iniciar nueva curva
                    self.curve_samples = 1
                    self.current_curve_direction = current_direction
                else:
                    self.curve_samples += 1
                    
        else:  # Volante recto
            if self.in_curve:
                self.cooldown_counter += 1
                
                # Terminar curva si superamos cooldown
                if self.cooldown_counter >= self.cooldown_samples:
                    if self.curve_samples >= self.min_duration:
                        curve_finished = True
                        curve_detected = True
                        self._register_curve(timestamp)
                    
                    # Resetear estado
                    self.in_curve = False
                    self.curve_samples = 0
                    self.current_curve_direction = None
        
        return {
            'in_curve': self.in_curve,
            'curve_direction': self.current_curve_direction,
            'curve_detected': curve_detected,
            'curve_finished': curve_finished,
            'total_curves': self.total_curves,
            'left_curves': self.left_curves,
            'right_curves': self.right_curves,
            'current_steer_angle': steer_angle
        }
    
    def _register_curve(self, timestamp: str = None):
        """Registra una curva completada"""
        self.total_curves += 1
        
        if self.current_curve_direction == 'left':
            self.left_curves += 1
        elif self.current_curve_direction == 'right':
            self.right_curves += 1
        
        # Guardar en log
        self.curves_log.append({
            'curve_number': self.total_curves,
            'direction': self.current_curve_direction,
            'duration_samples': self.curve_samples,
            'timestamp': timestamp
        })
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de curvas"""
        return {
            'total_curves': self.total_curves,
            'left_curves': self.left_curves,
            'right_curves': self.right_curves,
            'in_curve': self.in_curve,
            'current_direction': self.current_curve_direction
        }
    
    def reset(self):
        """Resetea el detector (útil para nueva vuelta)"""
        self.history.clear()
        self.in_curve = False
        self.curve_samples = 0
        self.cooldown_counter = 0
        self.current_curve_direction = None
        self.total_curves = 0
        self.left_curves = 0
        self.right_curves = 0
        self.curves_log = []


def analyze_telemetry_curves(telemetry_data: List[Dict]) -> Dict:
    """
    Analiza una sesión completa de telemetría para detectar curvas
    
    Args:
        telemetry_data: Lista de registros de telemetría
        
    Returns:
        Diccionario con análisis de curvas
    """
    detector = CurveDetector()
    
    for record in telemetry_data:
        player_data = record.get('player_telemetry')
        if player_data and 'steer_angle' in player_data:
            timestamp = record.get('timestamp')
            detector.update(player_data['steer_angle'], timestamp)
    
    return {
        'total_curves': detector.total_curves,
        'left_curves': detector.left_curves,
        'right_curves': detector.right_curves,
        'curves_log': detector.curves_log,
        'avg_curves_per_lap': 0  # Calcular si hay info de vueltas
    }
