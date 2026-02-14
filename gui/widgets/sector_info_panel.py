"""
Panel de información de sector seleccionado
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt
from typing import Dict
from gui.styles import COLORS


class SectorInfoPanel(QWidget):
    """Panel que muestra información detallada de un sector"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['panel_bg']};
                border: 2px solid {COLORS['accent']};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Título
        self.title_label = QLabel("Sector Seleccionado")
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {COLORS['accent']};
        """)
        layout.addWidget(self.title_label)
        
        # Grid de información
        grid = QGridLayout()
        grid.setSpacing(8)
        
        # Labels de info
        self.delta_label = self._create_info_label("Delta:", "")
        self.cumulative_label = self._create_info_label("Acumulado:", "")
        self.speed_avg_label = self._create_info_label("Vel. Media:", "")
        self.speed_min_label = self._create_info_label("Vel. Mínima:", "")
        self.brake_label = self._create_info_label("Uso de Freno:", "")
        self.throttle_label = self._create_info_label("Acelerador:", "")
        
        # Añadir al grid
        grid.addWidget(QLabel("Delta:"), 0, 0)
        grid.addWidget(self.delta_label, 0, 1)
        
        grid.addWidget(QLabel("Acumulado:"), 1, 0)
        grid.addWidget(self.cumulative_label, 1, 1)
        
        grid.addWidget(QLabel("Vel. Media:"), 2, 0)
        grid.addWidget(self.speed_avg_label, 2, 1)
        
        grid.addWidget(QLabel("Vel. Mínima:"), 3, 0)
        grid.addWidget(self.speed_min_label, 3, 1)
        
        grid.addWidget(QLabel("Uso Freno:"), 4, 0)
        grid.addWidget(self.brake_label, 4, 1)
        
        grid.addWidget(QLabel("Acelerador:"), 5, 0)
        grid.addWidget(self.throttle_label, 5, 1)
        
        # Estilo para labels
        for i in range(grid.rowCount()):
            label = grid.itemAtPosition(i, 0).widget()
            label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        
        layout.addLayout(grid)
        
        # Consejo
        self.advice_label = QLabel("")
        self.advice_label.setWordWrap(True)
        self.advice_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 11px;
            padding: 8px;
            background: {COLORS['input_bg']};
            border-radius: 4px;
            margin-top: 8px;
        """)
        layout.addWidget(self.advice_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        self.hide()  # Ocultar hasta que se seleccione un sector
        
    def _create_info_label(self, key: str, value: str) -> QLabel:
        """Crea un label de información"""
        label = QLabel(value)
        label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600; font-size: 12px;")
        return label
        
    def update_info(self, sector_num: int, sector_data: Dict):
        """
        Actualiza la información del sector
        
        Args:
            sector_num: Número de sector (0-based)
            sector_data: Datos del sector de la comparación
        """
        self.title_label.setText(f"📍 Sector {sector_num + 1}")
        
        # Delta
        delta = sector_data.get('delta', 0)
        delta_str = f"+{delta:.3f}s" if delta > 0 else f"{delta:.3f}s"
        self.delta_label.setText(delta_str)
        if delta > 0:
            self.delta_label.setStyleSheet(f"color: {QColor(255, 68, 68).name()}; font-weight: 600; font-size: 12px;")
        else:
            self.delta_label.setStyleSheet(f"color: {QColor(76, 209, 55).name()}; font-weight: 600; font-size: 12px;")
        
        # Acumulado
        cumul = sector_data.get('cumulative_delta', 0)
        cumul_str = f"+{cumul:.3f}s" if cumul > 0 else f"{cumul:.3f}s"
        self.cumulative_label.setText(cumul_str)
        
        # Velocidades
        speed_diff = sector_data.get('speed_diff', 0)
        self.speed_avg_label.setText(f"{speed_diff:+.1f} km/h")
        
        min_speed = sector_data.get('lap2_min_speed', 0)
        best_min_speed = sector_data.get('lap1_min_speed', 0)
        self.speed_min_label.setText(f"{min_speed:.1f} km/h (mejor: {best_min_speed:.1f})")
        
        # Uso de freno y acelerador (si está disponible)
        # Por ahora mostramos N/A
        self.brake_label.setText("N/A")
        self.throttle_label.setText("N/A")
        
        # Generar consejo
        advice = self._generate_advice(delta, speed_diff, min_speed, best_min_speed)
        self.advice_label.setText(f"💡 {advice}")
        
        self.show()
        
    def _generate_advice(self, delta: float, speed_diff: float, min_speed: float, best_min_speed: float) -> str:
        """Genera un consejo basado en los datos"""
        if delta < -0.01:
            return "¡Buen trabajo! Estás ganando tiempo en este sector."
        
        elif delta > 0.1:
            if speed_diff < -3:
                speed_loss = best_min_speed - min_speed
                if speed_loss > 5:
                    return f"Estás frenando demasiado fuerte. Intenta mantener {speed_loss:.0f} km/h más de velocidad mínima."
                else:
                    return "Tu velocidad media es baja. Intenta acelerar antes o frenar más tarde."
            elif min_speed < best_min_speed - 3:
                return "Tu velocidad mínima es baja. Prueba a frenar menos o tomar un apex más cerrado."
            else:
                return "Pierdes tiempo pero las velocidades son similares. Revisa la trazada o suaviza los inputs."
        
        else:
            return "Sector casi perfecto. Pequeños ajustes pueden mejorarlo."


from PySide6.QtGui import QColor
