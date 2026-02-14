"""
Widget de Mapa de Circuito 2D - Visualización de sectores y deltas (Interactivo)
"""

from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont, QCursor
from typing import List, Dict, Optional
import math


class TrackMapWidget(QWidget):
    """Widget que dibuja el mapa 2D del circuito con sectores (interactivo)"""
    
    # Señal emitida cuando se hace click en un sector
    sector_clicked = Signal(int)  # índice del sector (0-based)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)  # Para detectar hover
        
        # Datos del circuito
        self.track_points = []
        self.track_name = ""
        
        # Sectores
        self.num_sectors = 10
        self.sector_colors = []
        self.sector_deltas = []
        self.sector_data = []  # Datos adicionales por sector
        
        # Interactividad
        self.hovered_sector = -1
        self.selected_sector = -1
        
        # Posición actual
        self.current_position = 0.0
        self.show_current_position = False
        
        # Configuración visual
        self.bg_color = QColor("#1a202c")
        self.track_color = QColor("#4a5568")
        self.text_color = QColor("#e2e8f0")
        self.hover_color = QColor(255, 255, 255, 100)
        
        # Escala y offset
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Mapeo de sectores a regiones de pantalla
        self.sector_regions = []
        
    def set_track_data(self, track_points: List[tuple], track_name: str = ""):
        """Establece los puntos del circuito"""
        self.track_points = track_points
        self.track_name = track_name
        
        if track_points:
            self._calculate_scale_and_offset()
            self._calculate_sector_regions()
        
        self.update()
    
    def set_sector_analysis(self, num_sectors: int, deltas: List[float], sector_data: Optional[List[Dict]] = None):
        """
        Establece el análisis de sectores
        
        Args:
            num_sectors: Número de sectores
            deltas: Lista de deltas por sector
            sector_data: Datos adicionales por sector (velocidad, tiempo, etc.)
        """
        self.num_sectors = num_sectors
        self.sector_deltas = deltas
        self.sector_data = sector_data or []
        
        # Calcular colores según deltas
        self.sector_colors = []
        
        if deltas:
            max_abs_delta = max(abs(d) for d in deltas) if deltas else 1.0
            
            for delta in deltas:
                if delta > 0:
                    # Rojo - pierde tiempo
                    intensity = min(255, int(255 * (delta / max_abs_delta)))
                    color = QColor(255, max(0, 255 - intensity), max(0, 255 - intensity))
                else:
                    # Verde - gana tiempo
                    intensity = min(255, int(255 * (abs(delta) / max_abs_delta)))
                    color = QColor(max(0, 255 - intensity), 255, max(0, 255 - intensity))
                
                self.sector_colors.append(color)
        
        self._calculate_sector_regions()
        self.update()
    
    def set_current_position(self, position: float, show: bool = True):
        """Establece la posición actual en el circuito"""
        self.current_position = position
        self.show_current_position = show
        self.update()
    
    def _calculate_scale_and_offset(self):
        """Calcula la escala y offset para centrar el mapa"""
        if not self.track_points:
            return
        
        min_x = min(p[0] for p in self.track_points)
        max_x = max(p[0] for p in self.track_points)
        min_y = min(p[1] for p in self.track_points)
        max_y = max(p[1] for p in self.track_points)
        
        track_width = max_x - min_x
        track_height = max_y - min_y
        
        margin = 40
        available_width = self.width() - 2 * margin
        available_height = self.height() - 2 * margin - 40
        
        scale_x = available_width / track_width if track_width > 0 else 1.0
        scale_y = available_height / track_height if track_height > 0 else 1.0
        self.scale = min(scale_x, scale_y)
        
        self.offset_x = margin - min_x * self.scale + (available_width - track_width * self.scale) / 2
        self.offset_y = margin + 40 - min_y * self.scale + (available_height - track_height * self.scale) / 2
    
    def _world_to_screen(self, x: float, y: float) -> tuple:
        """Convierte coordenadas del mundo a coordenadas de pantalla"""
        screen_x = x * self.scale + self.offset_x
        screen_y = y * self.scale + self.offset_y
        return screen_x, screen_y
    
    def _calculate_sector_regions(self):
        """Calcula las regiones de pantalla para cada sector (para detección de click)"""
        self.sector_regions = []
        
        if not self.track_points or not self.num_sectors:
            return
        
        total_points = len(self.track_points)
        points_per_sector = total_points // self.num_sectors
        
        for sector_idx in range(self.num_sectors):
            start_idx = sector_idx * points_per_sector
            end_idx = start_idx + points_per_sector if sector_idx < self.num_sectors - 1 else total_points
            
            if end_idx > total_points:
                end_idx = total_points
            
            # Guardar puntos del sector en coordenadas de pantalla
            sector_points = []
            for i in range(start_idx, min(end_idx, total_points)):
                x, y = self._world_to_screen(self.track_points[i][0], self.track_points[i][1])
                sector_points.append((x, y))
            
            self.sector_regions.append(sector_points)
    
    def _get_sector_at_position(self, pos_x: float, pos_y: float) -> int:
        """Determina qué sector está en la posición del mouse"""
        if not self.sector_regions:
            return -1
        
        # Buscar el sector más cercano al punto
        min_distance = float('inf')
        closest_sector = -1
        threshold = 15  # Píxeles de tolerancia
        
        for sector_idx, sector_points in enumerate(self.sector_regions):
            for point_x, point_y in sector_points:
                distance = math.sqrt((point_x - pos_x)**2 + (point_y - pos_y)**2)
                if distance < min_distance and distance < threshold:
                    min_distance = distance
                    closest_sector = sector_idx
        
        return closest_sector
    
    def mouseMoveEvent(self, event):
        """Detecta hover sobre sectores"""
        pos = event.pos()
        hovered = self._get_sector_at_position(pos.x(), pos.y())
        
        if hovered != self.hovered_sector:
            self.hovered_sector = hovered
            self.update()
            
            # Mostrar tooltip con información del sector
            if hovered >= 0 and hovered < len(self.sector_deltas):
                delta = self.sector_deltas[hovered]
                delta_str = f"+{delta:.3f}s" if delta > 0 else f"{delta:.3f}s"
                
                tooltip_text = f"<b>Sector {hovered + 1}</b><br>"
                tooltip_text += f"Delta: {delta_str}"
                
                if self.sector_data and hovered < len(self.sector_data):
                    data = self.sector_data[hovered]
                    tooltip_text += f"<br>Vel. Media: {data.get('avg_speed', 0):.1f} km/h"
                    tooltip_text += f"<br>Vel. Mín: {data.get('min_speed', 0):.1f} km/h"
                
                QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
            else:
                QToolTip.hideText()
        
        # Cambiar cursor si está sobre un sector
        if hovered >= 0:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mousePressEvent(self, event):
        """Detecta click en sectores"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            clicked_sector = self._get_sector_at_position(pos.x(), pos.y())
            
            if clicked_sector >= 0:
                self.selected_sector = clicked_sector
                self.sector_clicked.emit(clicked_sector)
                self.update()
    
    def leaveEvent(self, event):
        """Cuando el mouse sale del widget"""
        self.hovered_sector = -1
        self.setCursor(Qt.CursorShape.ArrowCursor)
        QToolTip.hideText()
        self.update()
    
    def paintEvent(self, event):
        """Dibuja el mapa del circuito"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo
        painter.fillRect(self.rect(), self.bg_color)
        
        # Título
        if self.track_name:
            painter.setPen(self.text_color)
            font = QFont("Arial", 14, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(self.rect().adjusted(0, 5, 0, 0), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           self.track_name)
        
        if not self.track_points or len(self.track_points) < 2:
            painter.setPen(QColor("#718096"))
            font = QFont("Arial", 12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           "No hay datos de circuito\n\nCarga una telemetría para ver el mapa\n\nClick en sectores para ver detalles")
            return
        
        self._calculate_scale_and_offset()
        
        # Dibujar sectores con colores
        if self.sector_colors and len(self.sector_colors) == self.num_sectors:
            self._draw_colored_sectors(painter)
        else:
            self._draw_simple_track(painter)
        
        # Dibujar highlight del sector en hover
        if self.hovered_sector >= 0:
            self._draw_sector_highlight(painter, self.hovered_sector)
        
        # Dibujar selección del sector
        if self.selected_sector >= 0 and self.selected_sector != self.hovered_sector:
            self._draw_sector_selection(painter, self.selected_sector)
        
        # Dibujar divisiones de sectores
        self._draw_sector_divisions(painter)
        
        # Dibujar línea de meta/salida
        self._draw_start_finish_line(painter)
        
        # Dibujar posición actual si está habilitada
        if self.show_current_position:
            self._draw_current_position(painter)
        
        # Dibujar leyenda
        self._draw_legend(painter)
    
    def _draw_simple_track(self, painter: QPainter):
        """Dibuja el circuito sin colores de sectores"""
        pen = QPen(self.track_color)
        pen.setWidth(8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        path = QPainterPath()
        
        x, y = self._world_to_screen(self.track_points[0][0], self.track_points[0][1])
        path.moveTo(x, y)
        
        for point in self.track_points[1:]:
            x, y = self._world_to_screen(point[0], point[1])
            path.lineTo(x, y)
        
        x, y = self._world_to_screen(self.track_points[0][0], self.track_points[0][1])
        path.lineTo(x, y)
        
        painter.drawPath(path)
    
    def _draw_colored_sectors(self, painter: QPainter):
        """Dibuja el circuito con colores por sector"""
        total_points = len(self.track_points)
        points_per_sector = total_points // self.num_sectors
        
        for sector_idx in range(self.num_sectors):
            start_idx = sector_idx * points_per_sector
            end_idx = start_idx + points_per_sector if sector_idx < self.num_sectors - 1 else total_points
            
            if end_idx > total_points:
                end_idx = total_points
            
            color = self.sector_colors[sector_idx] if sector_idx < len(self.sector_colors) else self.track_color
            
            pen = QPen(color)
            pen.setWidth(8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            for i in range(start_idx, min(end_idx, total_points - 1)):
                x1, y1 = self._world_to_screen(self.track_points[i][0], self.track_points[i][1])
                x2, y2 = self._world_to_screen(self.track_points[i + 1][0], self.track_points[i + 1][1])
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_sector_highlight(self, painter: QPainter, sector_idx: int):
        """Dibuja highlight sobre el sector en hover"""
        if sector_idx >= len(self.sector_regions):
            return
        
        pen = QPen(self.hover_color)
        pen.setWidth(12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        sector_points = self.sector_regions[sector_idx]
        for i in range(len(sector_points) - 1):
            x1, y1 = sector_points[i]
            x2, y2 = sector_points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_sector_selection(self, painter: QPainter, sector_idx: int):
        """Dibuja borde alrededor del sector seleccionado"""
        if sector_idx >= len(self.sector_regions):
            return
        
        pen = QPen(QColor(68, 138, 255))
        pen.setWidth(14)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        sector_points = self.sector_regions[sector_idx]
        for i in range(len(sector_points) - 1):
            x1, y1 = sector_points[i]
            x2, y2 = sector_points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_sector_divisions(self, painter: QPainter):
        """Dibuja las líneas divisorias de sectores"""
        if not self.track_points:
            return
        
        pen = QPen(QColor(255, 255, 255, 150))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        total_points = len(self.track_points)
        points_per_sector = total_points // self.num_sectors
        
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        for sector_idx in range(1, self.num_sectors):
            point_idx = sector_idx * points_per_sector
            
            if point_idx >= total_points:
                continue
            
            x, y = self._world_to_screen(self.track_points[point_idx][0], 
                                        self.track_points[point_idx][1])
            
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(QPointF(x, y), 5, 5)
            
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(x + 10), int(y - 10), f"S{sector_idx + 1}")
            
            pen = QPen(QColor(255, 255, 255, 150))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
    
    def _draw_start_finish_line(self, painter: QPainter):
        """Dibuja la línea de salida/meta"""
        if not self.track_points:
            return
        
        x, y = self._world_to_screen(self.track_points[0][0], self.track_points[0][1])
        
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        flag_rect = QRectF(x - 8, y - 12, 16, 24)
        painter.drawRect(flag_rect)
        
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawRect(QRectF(x - 8, y - 12, 8, 12))
        painter.drawRect(QRectF(x, y, 8, 12))
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(int(x - 20), int(y + 30), "START")
    
    def _draw_current_position(self, painter: QPainter):
        """Dibuja el indicador de posición actual"""
        total_points = len(self.track_points)
        point_idx = int(self.current_position * total_points)
        point_idx = min(point_idx, total_points - 1)
        
        x, y = self._world_to_screen(self.track_points[point_idx][0], 
                                     self.track_points[point_idx][1])
        
        pen = QPen(QColor(68, 138, 255))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(68, 138, 255, 200)))
        painter.drawEllipse(QPointF(x, y), 8, 8)
        
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(x, y), 12, 12)
    
    def _draw_legend(self, painter: QPainter):
        """Dibuja la leyenda de colores"""
        if not self.sector_deltas:
            return
        
        legend_x = 10
        legend_y = self.height() - 80
        
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(legend_x, legend_y, 180, 70)
        
        painter.setPen(self.text_color)
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(legend_x + 10, legend_y + 15, "Leyenda:")
        
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        painter.setBrush(QBrush(QColor(76, 209, 55)))
        painter.drawRect(legend_x + 10, legend_y + 25, 15, 15)
        painter.drawText(legend_x + 30, legend_y + 37, "Gana tiempo")
        
        painter.setBrush(QBrush(QColor(255, 68, 68)))
        painter.drawRect(legend_x + 100, legend_y + 25, 15, 15)
        painter.drawText(legend_x + 120, legend_y + 37, "Pierde")
        
        # Instrucción de interacción
        font = QFont("Arial", 7)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(legend_x + 10, legend_y + 55, "💡 Click en sectores")
        painter.drawText(legend_x + 10, legend_y + 67, "    para ver detalles")
    
    def resizeEvent(self, event):
        """Cuando cambia el tamaño del widget"""
        super().resizeEvent(event)
        if self.track_points:
            self._calculate_scale_and_offset()
            self._calculate_sector_regions()


def generate_track_from_telemetry(telemetry_data: List[Dict]) -> List[tuple]:
    """Genera puntos del circuito a partir de datos de telemetría"""
    track_points = []
    
    for record in telemetry_data:
        session = record.get('session_info', {})
        norm_pos = session.get('normalized_position', 0.0)
        
        # Crear circuito circular como fallback
        angle = norm_pos * 2 * math.pi
        radius = 100
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        track_points.append((x, y))
    
    # Eliminar duplicados consecutivos
    filtered_points = []
    for i, point in enumerate(track_points):
        if i == 0 or point != track_points[i - 1]:
            filtered_points.append(point)
    
    return filtered_points
