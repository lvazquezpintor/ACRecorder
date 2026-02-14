"""
Widget de Mapa 2D del Circuito - Visualiza la trazada y sectores
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPainterPath
from typing import List, Dict, Tuple
import math


class TrackMapWidget(QWidget):
    """
    Widget que dibuja un mapa 2D del circuito basado en la telemetría
    Usa normalized_position y velocidad para reconstruir la trazada
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)
        
        # Datos del circuito
        self.track_points = []  # Lista de (x, y, speed, sector)
        self.sector_boundaries = []  # Posiciones donde cambia de sector
        self.sector_deltas = []  # Deltas por sector (color-coded)
        
        # Configuración visual
        self.track_color = QColor(60, 60, 60)
        self.fast_color = QColor(76, 209, 55)  # Verde para rápido
        self.slow_color = QColor(255, 68, 68)  # Rojo para lento
        self.neutral_color = QColor(100, 100, 100)  # Gris para neutral
        
        # Punto actual siendo analizado
        self.current_position = None
        
        # Zoom y pan
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
    def set_track_data(self, lap_data: List[Dict]):
        """
        Construye el mapa del circuito desde datos de telemetría
        
        Args:
            lap_data: Lista de registros de telemetría de una vuelta
        """
        if not lap_data:
            return
        
        self.track_points = []
        
        # Construir trazada usando normalized_position como ángulo
        # y velocidad como radio (cuanto más rápido, más al exterior)
        for record in lap_data:
            session = record.get('session_info', {})
            player = record.get('player_telemetry', {})
            
            norm_pos = session.get('normalized_position', 0.0)
            speed = player.get('speed_kmh', 0)
            sector = session.get('current_sector', 0)
            
            # Convertir normalized_position a ángulo (0-360 grados)
            angle = norm_pos * 2 * math.pi
            
            # Usar velocidad normalizada como factor de escala
            # Añadir offset base para que el circuito no colapse
            base_radius = 200
            speed_factor = speed / 300  # Normalizar a máximo de 300 km/h
            radius = base_radius * (0.7 + 0.3 * speed_factor)
            
            # Calcular coordenadas X, Y
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            self.track_points.append({
                'x': x,
                'y': y,
                'speed': speed,
                'sector': sector,
                'norm_pos': norm_pos
            })
        
        self.update()
    
    def set_sector_deltas(self, deltas: List[Dict]):
        """
        Establece los deltas por sector para colorear el mapa
        
        Args:
            deltas: Lista con información de deltas por sector
                   Cada dict debe tener: segment, delta, percentage
        """
        self.sector_deltas = deltas
        self.update()
    
    def set_current_position(self, normalized_pos: float):
        """Marca la posición actual en el mapa"""
        self.current_position = normalized_pos
        self.update()
    
    def paintEvent(self, event):
        """Dibuja el mapa del circuito"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo
        painter.fillRect(self.rect(), QColor(20, 20, 25))
        
        if not self.track_points:
            # Mensaje si no hay datos
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           "Carga telemetría para ver el mapa")
            return
        
        # Configurar transformación (centrar y escalar)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self.zoom, self.zoom)
        painter.translate(self.offset_x, self.offset_y)
        
        # Dibujar líneas de sectores
        self.draw_sector_lines(painter)
        
        # Dibujar trazada coloreada por delta
        self.draw_track_with_deltas(painter)
        
        # Dibujar marcadores de sector
        self.draw_sector_markers(painter)
        
        # Dibujar posición actual
        if self.current_position is not None:
            self.draw_current_position(painter)
        
        # Dibujar leyenda
        painter.resetTransform()
        self.draw_legend(painter)
    
    def draw_track_with_deltas(self, painter: QPainter):
        """Dibuja la trazada coloreada según deltas"""
        if len(self.track_points) < 2:
            return
        
        # Determinar color para cada segmento
        num_segments = len(self.sector_deltas) if self.sector_deltas else 1
        
        for i in range(len(self.track_points) - 1):
            p1 = self.track_points[i]
            p2 = self.track_points[i + 1]
            
            # Determinar a qué segmento pertenece
            if self.sector_deltas:
                segment_idx = int(p1['norm_pos'] * num_segments)
                segment_idx = min(segment_idx, num_segments - 1)
                
                # Obtener delta del segmento
                if 0 <= segment_idx < len(self.sector_deltas):
                    delta = self.sector_deltas[segment_idx].get('delta', 0)
                    
                    # Colorear según delta
                    if abs(delta) < 0.02:  # Prácticamente igual
                        color = self.neutral_color
                    elif delta > 0:  # Pierdes tiempo
                        # Interpolar de amarillo a rojo según magnitud
                        intensity = min(abs(delta) / 0.2, 1.0)  # 0.2s = rojo completo
                        r = 255
                        g = int(255 * (1 - intensity * 0.8))  # De 255 a ~50
                        color = QColor(r, g, 0)
                    else:  # Ganas tiempo
                        # Interpolar de amarillo a verde según magnitud
                        intensity = min(abs(delta) / 0.2, 1.0)
                        r = int(255 * (1 - intensity))
                        g = 255
                        color = QColor(r, g, 0)
                else:
                    color = self.neutral_color
            else:
                # Sin deltas, colorear por velocidad
                speed_norm = min(p1['speed'] / 300, 1.0)
                r = int(255 * (1 - speed_norm))
                g = int(255 * speed_norm)
                color = QColor(r, g, 0)
            
            # Dibujar segmento
            pen = QPen(color)
            pen.setWidth(4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            painter.drawLine(
                int(p1['x']), int(p1['y']),
                int(p2['x']), int(p2['y'])
            )
    
    def draw_sector_lines(self, painter: QPainter):
        """Dibuja líneas divisorias de sectores"""
        if not self.sector_deltas:
            return
        
        num_segments = len(self.sector_deltas)
        
        for i in range(num_segments):
            # Posición normalizada del inicio del sector
            sector_pos = i / num_segments
            
            # Encontrar punto más cercano a esta posición
            closest_point = min(self.track_points, 
                              key=lambda p: abs(p['norm_pos'] - sector_pos))
            
            # Dibujar línea desde el centro hasta el punto
            pen = QPen(QColor(100, 100, 100, 100))
            pen.setWidth(1)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            
            painter.drawLine(0, 0, int(closest_point['x']), int(closest_point['y']))
    
    def draw_sector_markers(self, painter: QPainter):
        """Dibuja números y etiquetas de sectores"""
        if not self.sector_deltas:
            return
        
        num_segments = len(self.sector_deltas)
        
        for i, sector_data in enumerate(self.sector_deltas):
            # Posición en el medio del sector
            mid_pos = (i + 0.5) / num_segments
            
            # Encontrar punto representativo
            closest_point = min(self.track_points, 
                              key=lambda p: abs(p['norm_pos'] - mid_pos))
            
            # Extender un poco hacia afuera para la etiqueta
            factor = 1.25
            label_x = int(closest_point['x'] * factor)
            label_y = int(closest_point['y'] * factor)
            
            # Dibujar círculo de fondo
            delta = sector_data.get('delta', 0)
            if abs(delta) < 0.02:
                bg_color = self.neutral_color
            elif delta > 0:
                bg_color = QColor(255, 100, 100)
            else:
                bg_color = QColor(100, 255, 100)
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawEllipse(QPointF(label_x, label_y), 15, 15)
            
            # Dibujar número del sector
            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = QRectF(label_x - 15, label_y - 15, 30, 30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, 
                           str(sector_data['segment']))
            
            # Dibujar delta debajo
            delta_text = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
            font.setPixelSize(10)
            painter.setFont(font)
            painter.setPen(QColor(200, 200, 200))
            text_rect = QRectF(label_x - 30, label_y + 15, 60, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, delta_text)
    
    def draw_current_position(self, painter: QPainter):
        """Dibuja marcador de posición actual"""
        if self.current_position is None:
            return
        
        # Encontrar punto más cercano
        closest_point = min(self.track_points, 
                          key=lambda p: abs(p['norm_pos'] - self.current_position))
        
        # Dibujar marcador pulsante
        painter.setBrush(QBrush(QColor(68, 138, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawEllipse(QPointF(closest_point['x'], closest_point['y']), 8, 8)
    
    def draw_legend(self, painter: QPainter):
        """Dibuja leyenda explicativa"""
        # Leyenda en esquina superior derecha
        legend_x = self.width() - 180
        legend_y = 20
        
        painter.setPen(QColor(150, 150, 150))
        painter.setBrush(QBrush(QColor(30, 30, 35, 230)))
        painter.drawRoundedRect(legend_x, legend_y, 160, 120, 8, 8)
        
        # Título
        font = QFont()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(legend_x + 10, legend_y + 20, "Deltas por Sector")
        
        # Elementos de leyenda
        font.setBold(False)
        font.setPixelSize(11)
        painter.setFont(font)
        
        items = [
            (QColor(100, 255, 100), "Ganas tiempo"),
            (QColor(255, 255, 100), "Similar (~0.02s)"),
            (QColor(255, 100, 100), "Pierdes tiempo")
        ]
        
        y_offset = 45
        for color, text in items:
            # Cuadrado de color
            painter.setBrush(QBrush(color))
            painter.setPen(QColor(100, 100, 100))
            painter.drawRect(legend_x + 10, legend_y + y_offset - 8, 15, 15)
            
            # Texto
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(legend_x + 32, legend_y + y_offset + 4, text)
            
            y_offset += 25
    
    def wheelEvent(self, event):
        """Maneja zoom con rueda del ratón"""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom *= 0.9
        
        self.zoom = max(0.5, min(3.0, self.zoom))
        self.update()
    
    def mousePressEvent(self, event):
        """Inicia pan con ratón"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        """Pan con arrastre del ratón"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            if hasattr(self, 'last_mouse_pos'):
                delta = event.pos() - self.last_mouse_pos
                self.offset_x += delta.x() / self.zoom
                self.offset_y += delta.y() / self.zoom
                self.last_mouse_pos = event.pos()
                self.update()
    
    def reset_view(self):
        """Resetea zoom y pan"""
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update()
