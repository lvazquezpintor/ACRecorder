"""
Pestaña de Control - Monitoreo y grabación
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTextEdit
from PySide6.QtCore import Signal
from datetime import datetime

from gui.widgets import ModernButton, StatusIndicator, DataCard
from gui.styles import COLORS, PANEL_STYLE, PANEL_TITLE_STYLE, TEXT_EDIT_STYLE, STATUS_LABEL_STYLE


class ControlTab(QWidget):
    """Pestaña de control principal"""
    
    # Señales para comunicación con la ventana principal
    start_monitoring_requested = Signal()
    stop_monitoring_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Panel de estado
        status_panel = self.create_status_panel()
        layout.addWidget(status_panel)
        
        # Panel de datos de sesión
        session_panel = self.create_session_panel()
        layout.addWidget(session_panel)
        
        # Event Log
        log_panel = self.create_log_panel()
        layout.addWidget(log_panel, stretch=1)
        
        self.setLayout(layout)
        
    def create_status_panel(self) -> QFrame:
        """Crea el panel de estado del sistema"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Título
        title = QLabel("System Status")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        
        # Indicador de estado
        status_row = QHBoxLayout()
        self.status_indicator = StatusIndicator(COLORS['status_offline'])
        self.status_text = QLabel("System Offline")
        self.status_text.setStyleSheet(STATUS_LABEL_STYLE)
        
        status_row.addWidget(self.status_indicator)
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        
        # Botones de control
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)
        
        self.btn_start = ModernButton("▶  START MONITORING", primary=True)
        self.btn_start.clicked.connect(self.start_monitoring_requested.emit)
        
        self.btn_stop = ModernButton("⏹  STOP", danger=True)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_monitoring_requested.emit)
        
        buttons_row.addWidget(self.btn_start)
        buttons_row.addWidget(self.btn_stop)
        buttons_row.addStretch()
        
        # Ensamblar panel
        layout.addWidget(title)
        layout.addLayout(status_row)
        layout.addLayout(buttons_row)
        
        panel.setLayout(layout)
        return panel
        
    def create_session_panel(self) -> QFrame:
        """Crea el panel de datos de sesión"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        title = QLabel("Session Data")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(title)
        
        # Cards de datos
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.card_duration = DataCard("DURATION", "00:00:00")
        self.card_records = DataCard("RECORDS", "0")
        self.card_session = DataCard("SESSION", "—")
        
        cards_layout.addWidget(self.card_duration)
        cards_layout.addWidget(self.card_records)
        cards_layout.addWidget(self.card_session, stretch=1)
        
        layout.addLayout(cards_layout)
        
        panel.setLayout(layout)
        return panel
        
    def create_log_panel(self) -> QFrame:
        """Crea el panel de log de eventos"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        title = QLabel("Event Log")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(TEXT_EDIT_STYLE)
        
        layout.addWidget(title)
        layout.addWidget(self.log_text)
        
        panel.setLayout(layout)
        return panel
        
    # ========== Métodos públicos para la ventana principal ==========
    
    def set_monitoring_active(self, active: bool):
        """Actualiza el estado de los botones"""
        self.btn_start.setEnabled(not active)
        self.btn_stop.setEnabled(active)
        
    def set_status(self, text: str, color: str):
        """Actualiza el texto e indicador de estado"""
        self.status_text.setText(text)
        self.status_indicator.set_color(color)
        
    def log(self, message: str):
        """Añade un mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}]  {message}")
        
    def update_duration(self, duration_text: str):
        """Actualiza la duración mostrada"""
        self.card_duration.set_value(duration_text)
        
    def update_records(self, count: int):
        """Actualiza el contador de registros"""
        self.card_records.set_value(str(count))
        
    def update_session_name(self, name: str):
        """Actualiza el nombre de sesión"""
        self.card_session.set_value(name)
