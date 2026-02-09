"""
ACC Race Recorder - Modern Qt6 GUI Complete
Diseño moderno y limpio con todas las funcionalidades integradas
"""

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFrame, 
                               QStackedWidget, QTextEdit, QTreeWidget, QTreeWidgetItem,
                               QComboBox, QLineEdit, QFileDialog, QMessageBox,
                               QHeaderView)
from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QFont, QPalette, QColor, QPainter
import sys
import threading
import time
import json
import subprocess
import os
import webbrowser
from datetime import datetime
from pathlib import Path

# Importar módulos del proyecto
try:
    import psutil
except ImportError:
    psutil = None

class ModernButton(QPushButton):
    """Botón moderno personalizado"""
    def __init__(self, text, primary=False, danger=False, success=False):
        super().__init__(text)
        self.primary = primary
        self.danger = danger
        self.success = success
        self.setup_style()
        
    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2D3748;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #1A202C;
                }
                QPushButton:disabled {
                    background-color: #E2E8F0;
                    color: #A0AEC0;
                }
            """)
        elif self.success:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #48BB78;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #38A169;
                }
            """)
        elif self.danger:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F7FAFC;
                    color: #4A5568;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #EDF2F7;
                    border-color: #CBD5E0;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F7FAFC;
                    color: #4A5568;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #EDF2F7;
                }
            """)

class SidebarButton(QPushButton):
    """Botón de navegación lateral"""
    def __init__(self, icon_text, text):
        super().__init__(f"{icon_text}  {text}")
        self.setCheckable(True)
        self.setup_style()
        
    def setup_style(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A5568;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F7FAFC;
            }
            QPushButton:checked {
                background-color: #F7FAFC;
                border-left: 3px solid #E53E3E;
                color: #2D3748;
            }
        """)

class StatusIndicator(QWidget):
    """Indicador de estado circular"""
    def __init__(self, color="#EF4444"):
        super().__init__()
        self.color = color
        self.setFixedSize(12, 12)
        
    def set_color(self, color):
        self.color = color
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 12, 12)

class DataCard(QFrame):
    """Tarjeta de datos"""
    def __init__(self, label, value="—"):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #718096; font-size: 12px; font-weight: 500;")
        
        self.value_widget = QLabel(value)
        self.value_widget.setStyleSheet("color: #2D3748; font-size: 20px; font-weight: 600;")
        
        layout.addWidget(label_widget)
        layout.addWidget(self.value_widget)
        self.setLayout(layout)
        
    def set_value(self, value):
        self.value_widget.setText(str(value))

class ACCRecorderModern(QMainWindow):
    """Aplicación principal con diseño moderno"""
    
    def __init__(self):
        super().__init__()
        
        # Variables de estado
        self.is_monitoring = False
        self.is_recording = False
        self.monitor_thread = None
        self.recording_thread = None
        self.telemetry_thread = None
        self.ffmpeg_process = None
        self.recording_start_time = None
        self.output_dir = Path.home() / "ACC_Recordings"
        self.current_session_dir = None
        self.telemetry_data = []
        
        # Variables de configuración
        self.fps_var = "30"
        self.crf_var = "23"
        self.preset_var = "ultrafast"
        self.interval_var = "1"
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup UI
        self.setWindowTitle("ACC Race Recorder")
        self.setMinimumSize(1200, 800)
        
        self.setup_ui()
        
        # Timer para actualizar duración
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)
        self.timer.start(1000)
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Contenido principal
        content = self.create_content_area()
        main_layout.addWidget(content, stretch=1)
        
        central.setLayout(main_layout)
        
        self.setStyleSheet("QMainWindow { background-color: #F7FAFC; }")
        
    def create_sidebar(self):
        """Crea la barra lateral de navegación"""
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-right: 1px solid #E2E8F0;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #E2E8F0;")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(20, 24, 20, 24)
        
        avatar = QLabel("👤")
        avatar.setStyleSheet("""
            font-size: 32px;
            background-color: #EDF2F7;
            border-radius: 32px;
            padding: 16px;
        """)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(64, 64)
        
        title = QLabel("ACC\nRECORDER")
        title.setStyleSheet("color: #2D3748; font-size: 16px; font-weight: 700; margin-top: 12px;")
        title.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(avatar, alignment=Qt.AlignCenter)
        header_layout.addWidget(title, alignment=Qt.AlignCenter)
        header.setLayout(header_layout)
        
        layout.addWidget(header)
        
        # Navegación
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(0, 16, 0, 0)
        nav_layout.setSpacing(4)
        
        self.nav_buttons = []
        
        btn_control = SidebarButton("🏁", "CONTROL")
        btn_control.setChecked(True)
        btn_control.clicked.connect(lambda: self.switch_page(0))
        self.nav_buttons.append(btn_control)
        
        btn_sessions = SidebarButton("📄", "SESSIONS")
        btn_sessions.clicked.connect(lambda: self.switch_page(1))
        self.nav_buttons.append(btn_sessions)
        
        btn_analytics = SidebarButton("📊", "ANALYTICS")
        btn_analytics.clicked.connect(lambda: self.switch_page(2))
        self.nav_buttons.append(btn_analytics)
        
        btn_settings = SidebarButton("⚙️", "SETTINGS")
        btn_settings.clicked.connect(lambda: self.switch_page(3))
        self.nav_buttons.append(btn_settings)
        
        nav_layout.addWidget(btn_control)
        nav_layout.addWidget(btn_sessions)
        nav_layout.addWidget(btn_analytics)
        nav_layout.addWidget(btn_settings)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
        
        # Footer
        version = QLabel("VERSION 1.0.1")
        version.setStyleSheet("color: #A0AEC0; font-size: 11px; padding: 20px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        sidebar.setLayout(layout)
        return sidebar
        
    def create_content_area(self):
        """Crea el área de contenido principal"""
        container = QFrame()
        container.setStyleSheet("background-color: #F7FAFC;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        header = self.create_header()
        layout.addWidget(header)
        
        self.pages = QStackedWidget()
        
        self.pages.addWidget(self.create_control_page())
        self.pages.addWidget(self.create_sessions_page())
        self.pages.addWidget(self.create_analytics_page())
        self.pages.addWidget(self.create_settings_page())
        
        layout.addWidget(self.pages)
        
        container.setLayout(layout)
        return container
        
    def create_header(self):
        """Crea el header con búsqueda"""
        header = QFrame()
        header.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.page_title = QLabel("System Status")
        self.page_title.setStyleSheet("color: #2D3748; font-size: 24px; font-weight: 700;")
        
        layout.addWidget(self.page_title)
        layout.addStretch()
        
        # Search bar
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        search_container.setFixedWidth(300)
        
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 8, 12, 8)
        
        search_icon = QLabel("🔍")
        search_input = QLineEdit()
        search_input.setPlaceholderText("Find here...")
        search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #2D3748;
                font-size: 13px;
            }
        """)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(search_input)
        search_container.setLayout(search_layout)
        
        layout.addWidget(search_container)
        
        # Iconos de acción
        btn_notifications = QPushButton("🔔")
        btn_notifications.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #F7FAFC;
            }
        """)
        
        btn_settings_quick = QPushButton("⚙️")
        btn_settings_quick.setStyleSheet(btn_notifications.styleSheet())
        
        layout.addWidget(btn_notifications)
        layout.addWidget(btn_settings_quick)
        
        header.setLayout(layout)
        return header
        
    def create_control_page(self):
        """Página de control"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Panel de estado
        status_panel = QFrame()
        status_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(24, 20, 24, 20)
        status_layout.setSpacing(16)
        
        panel_title = QLabel("System Status")
        panel_title.setStyleSheet("color: #2D3748; font-size: 18px; font-weight: 600;")
        
        status_row = QHBoxLayout()
        self.status_indicator = StatusIndicator("#EF4444")
        self.status_text = QLabel("System Offline")
        self.status_text.setStyleSheet("color: #4A5568; font-size: 15px; font-weight: 500; margin-left: 8px;")
        
        status_row.addWidget(self.status_indicator)
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)
        
        self.btn_start = ModernButton("▶  START MONITORING", primary=True)
        self.btn_start.clicked.connect(self.start_monitoring)
        
        self.btn_stop = ModernButton("⏹  STOP", danger=True)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_monitoring)
        
        buttons_row.addWidget(self.btn_start)
        buttons_row.addWidget(self.btn_stop)
        buttons_row.addStretch()
        
        status_layout.addWidget(panel_title)
        status_layout.addLayout(status_row)
        status_layout.addLayout(buttons_row)
        
        status_panel.setLayout(status_layout)
        layout.addWidget(status_panel)
        
        # Panel de datos de sesión
        session_panel = QFrame()
        session_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        
        session_layout = QVBoxLayout()
        session_layout.setContentsMargins(24, 20, 24, 20)
        session_layout.setSpacing(16)
        
        session_title = QLabel("Session Data")
        session_title.setStyleSheet("color: #2D3748; font-size: 18px; font-weight: 600;")
        session_layout.addWidget(session_title)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.card_duration = DataCard("DURATION", "00:00:00")
        self.card_records = DataCard("RECORDS", "0")
        self.card_session = DataCard("SESSION", "—")
        
        cards_layout.addWidget(self.card_duration)
        cards_layout.addWidget(self.card_records)
        cards_layout.addWidget(self.card_session, stretch=1)
        
        session_layout.addLayout(cards_layout)
        session_panel.setLayout(session_layout)
        layout.addWidget(session_panel)
        
        # Event Log
        log_panel = QFrame()
        log_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(24, 20, 24, 20)
        log_layout.setSpacing(16)
        
        log_title = QLabel("Event Log")
        log_title.setStyleSheet("color: #2D3748; font-size: 18px; font-weight: 600;")
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #F7FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                color: #4A5568;
                font-family: 'Menlo', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        
        log_layout.addWidget(log_title)
        log_layout.addWidget(self.log_text)
        log_panel.setLayout(log_layout)
        layout.addWidget(log_panel, stretch=1)
        
        page.setLayout(layout)
        return page
        
    def create_sessions_page(self):
        """Página de sesiones grabadas"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Botones de acción
        btn_frame = QHBoxLayout()
        btn_frame.setSpacing(12)
        
        btn_refresh = ModernButton("🔄  REFRESH")
        btn_refresh.clicked.connect(self.refresh_recordings)
        
        btn_open_folder = ModernButton("📂  OPEN FOLDER")
        btn_open_folder.clicked.connect(self.open_recordings_folder)
        
        btn_frame.addWidget(btn_refresh)
        btn_frame.addWidget(btn_open_folder)
        btn_frame.addStretch()
        
        layout.addLayout(btn_frame)
        
        # Panel con lista de grabaciones
        list_panel = QFrame()
        list_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # TreeWidget
        self.recordings_tree = QTreeWidget()
        self.recordings_tree.setHeaderLabels(['Session', 'Date', 'Duration', 'Size'])
        self.recordings_tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: none;
                border-radius: 12px;
                color: #2D3748;
                font-size: 13px;
                padding: 12px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F7FAFC;
            }
            QTreeWidget::item:selected {
                background-color: #EDF2F7;
                color: #2D3748;
            }
            QHeaderView::section {
                background-color: #F7FAFC;
                color: #718096;
                padding: 12px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }
        """)
        
        # Configurar columnas
        header = self.recordings_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        list_layout.addWidget(self.recordings_tree)
        list_panel.setLayout(list_layout)
        layout.addWidget(list_panel, stretch=1)
        
        # Botones de acción con selección
        action_frame = QHBoxLayout()
        action_frame.setSpacing(12)
        
        btn_play = ModernButton("▶  PLAY VIDEO", success=True)
        btn_play.clicked.connect(self.play_selected_video)
        
        btn_view_data = ModernButton("📊  VIEW DATA", primary=True)
        btn_view_data.clicked.connect(self.view_selected_telemetry)
        
        btn_open_session = ModernButton("📁  OPEN FOLDER")
        btn_open_session.clicked.connect(self.open_selected_folder)
        
        action_frame.addWidget(btn_play)
        action_frame.addWidget(btn_view_data)
        action_frame.addWidget(btn_open_session)
        action_frame.addStretch()
        
        layout.addLayout(action_frame)
        
        page.setLayout(layout)
        
        # Cargar grabaciones iniciales
        self.refresh_recordings()
        
        return page
        
    def create_analytics_page(self):
        """Página de analytics"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Botones
        btn_frame = QHBoxLayout()
        btn_frame.setSpacing(12)
        
        btn_load = ModernButton("📂  LOAD JSON", primary=True)
        btn_load.clicked.connect(self.load_telemetry_json)
        
        btn_web = ModernButton("🌐  WEB VIEWER")
        btn_web.clicked.connect(self.open_web_viewer)
        
        btn_frame.addWidget(btn_load)
        btn_frame.addWidget(btn_web)
        btn_frame.addStretch()
        
        layout.addLayout(btn_frame)
        
        # Info
        self.telemetry_info = QLabel("No telemetry loaded")
        self.telemetry_info.setStyleSheet("color: #718096; font-size: 14px;")
        layout.addWidget(self.telemetry_info)
        
        # Stats panel
        stats_panel = QFrame()
        stats_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(24, 20, 24, 20)
        stats_layout.setSpacing(16)
        
        stats_title = QLabel("Quick Stats")
        stats_title.setStyleSheet("color: #2D3748; font-size: 18px; font-weight: 600;")
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #F7FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                color: #4A5568;
                font-family: 'Menlo', 'Monaco', monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        
        stats_layout.addWidget(stats_title)
        stats_layout.addWidget(self.stats_text)
        stats_panel.setLayout(stats_layout)
        layout.addWidget(stats_panel, stretch=1)
        
        page.setLayout(layout)
        return page
        
    def create_settings_page(self):
        """Página de configuración"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Video settings panel
        video_panel = QFrame()
        video_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(24, 20, 24, 20)
        video_layout.setSpacing(16)
        
        video_title = QLabel("Video Recording")
        video_title.setStyleSheet("color: #2D3748; font-size: 18px; font-weight: 600;")
        video_layout.addWidget(video_title)
        
        # FPS
        fps_row = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("color: #4A5568; font-size: 14px; min-width: 120px;")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(['24', '30', '60'])
        self.fps_combo.setCurrentText(self.fps_var)
        self.fps_combo.setStyleSheet("""
            QComboBox {
                background-color: #F7FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px 12px;
                color: #2D3748;
                font-size: 13px;
            }
        """)
        fps_row.addWidget(fps_label)
        fps_row.addWidget(self.fps_combo)
        fps_row.addStretch()
        video_layout.addLayout(fps_row)
        
        # CRF
        crf_row = QHBoxLayout()
        crf_label = QLabel("Quality (CRF):")
        crf_label.setStyleSheet("color: #4A5568; font-size: 14px; min-width: 120px;")
        self.crf_combo = QComboBox()
        self.crf_combo.addItems(['18', '23', '28'])
        self.crf_combo.setCurrentText(self.crf_var)
        self.crf_combo.setStyleSheet(self.fps_combo.styleSheet())
        crf_hint = QLabel("(18=High, 23=Medium, 28=Low)")
        crf_hint.setStyleSheet("color: #A0AEC0; font-size: 12px;")
        crf_row.addWidget(crf_label)
        crf_row.addWidget(self.crf_combo)
        crf_row.addWidget(crf_hint)
        crf_row.addStretch()
        video_layout.addLayout(crf_row)
        
        # Preset
        preset_row = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_label.setStyleSheet("color: #4A5568; font-size: 14px; min-width: 120px;")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['ultrafast', 'fast', 'medium'])
        self.preset_combo.setCurrentText(self.preset_var)
        self.preset_combo.setStyleSheet(self.fps_combo.styleSheet())
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.preset_combo)
        preset_row.addStretch()
        video_layout.addLayout(preset_row)
        
        video_panel.setLayout(video_layout)
        layout.addWidget(video_panel)
        
        # Telemetry settings panel
        telem_panel = QFrame()
        telem_panel.setStyleSheet(video_panel.styleSheet())
        
        telem_layout = QVBoxLayout()
        telem_layout.setContentsMargins(24, 20, 24, 20)
        telem_layout.setSpacing(16)
        
        telem_title = QLabel("Telemetry Capture")
        telem_title.setStyleSheet("color: #2D3748; font-size: 18px; font-weight: 600;")
        telem_layout.addWidget(telem_title)
        
        interval_row = QHBoxLayout()
        interval_label = QLabel("Interval (sec):")
        interval_label.setStyleSheet("color: #4A5568; font-size: 14px; min-width: 120px;")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['0.5', '1', '2'])
        self.interval_combo.setCurrentText(self.interval_var)
        self.interval_combo.setStyleSheet(self.fps_combo.styleSheet())
        interval_row.addWidget(interval_label)
        interval_row.addWidget(self.interval_combo)
        interval_row.addStretch()
        telem_layout.addLayout(interval_row)
        
        telem_panel.setLayout(telem_layout)
        layout.addWidget(telem_panel)
        
        # Output directory
        dir_panel = QFrame()
        dir_panel.setStyleSheet(video_panel.styleSheet())
        
        dir_layout = QVBoxLayout()
        dir_layout.setContentsMargins(24, 20, 24, 20)
        dir_layout.setSpacing(16)
        
        dir_title = QLabel("Output Directory")
        dir_title.setStyleSheet("color: #2D3748; font-size: 18px; font-weight: 600;")
        dir_layout.addWidget(dir_title)
        
        dir_row = QHBoxLayout()
        self.output_dir_label = QLabel(str(self.output_dir))
        self.output_dir_label.setStyleSheet("color: #4A5568; font-size: 13px;")
        btn_change_dir = ModernButton("Change")
        btn_change_dir.clicked.connect(self.change_output_dir)
        dir_row.addWidget(self.output_dir_label)
        dir_row.addWidget(btn_change_dir)
        dir_layout.addLayout(dir_row)
        
        dir_panel.setLayout(dir_layout)
        layout.addWidget(dir_panel)
        
        # Save button
        btn_save = ModernButton("💾  SAVE CONFIGURATION", success=True)
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)
        
        layout.addStretch()
        
        page.setLayout(layout)
        return page
        
    def switch_page(self, index):
        """Cambia entre páginas"""
        self.pages.setCurrentIndex(index)
        
        titles = ["System Status", "Recorded Sessions", "Telemetry Analytics", "System Settings"]
        self.page_title.setText(titles[index])
        
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            
    # ==================== MÉTODOS DE CONTROL ====================
    
    def start_monitoring(self):
        """Inicia el monitoreo"""
        self.is_monitoring = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.status_indicator.set_color("#F59E0B")
        self.status_text.setText("System Monitoring")
        
        self.log("✓ Monitoring started - Waiting for ACC...")
        
        self.monitor_thread = threading.Thread(target=self.monitor_acc, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_monitoring = False
        
        if self.is_recording:
            self.stop_recording()
            
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        self.status_indicator.set_color("#EF4444")
        self.status_text.setText("System Offline")
        
        self.log("✗ Monitoring stopped")
        
    def monitor_acc(self):
        """Monitorea ACC"""
        self.log("ACC monitoring thread started...")
        
        if not psutil:
            self.log("⚠ psutil not installed - cannot monitor ACC process")
            return
        
        while self.is_monitoring:
            try:
                acc_running = self.is_acc_running()
                
                if acc_running and not self.is_recording:
                    self.log("⚑ ACC detected - Starting recording")
                    self.start_recording()
                elif not acc_running and self.is_recording:
                    self.log("ACC closed - Stopping recording")
                    self.stop_recording()
                    
            except Exception as e:
                self.log(f"Error in monitoring: {str(e)}")
            
            time.sleep(2)
        
    def is_acc_running(self):
        """Verifica si ACC está corriendo"""
        if not psutil:
            return False
            
        for proc in psutil.process_iter(['name']):
            try:
                if 'AC2' in proc.info['name'] or 'Assetto' in proc.info['name']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
        
    def start_recording(self):
        """Inicia la grabación"""
        self.is_recording = True
        self.recording_start_time = datetime.now()
        
        session_name = self.recording_start_time.strftime("ACC_%Y%m%d_%H%M%S")
        self.current_session_dir = self.output_dir / session_name
        self.current_session_dir.mkdir(exist_ok=True)
        
        self.status_indicator.set_color("#10B981")
        self.status_text.setText("Recording Active")
        self.card_session.set_value(session_name)
        
        self.log(f"🔴 Recording started: {session_name}")
        
        # Start recording threads
        self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
        self.recording_thread.start()
        
        self.telemetry_data = []
        self.telemetry_thread = threading.Thread(target=self.record_telemetry, daemon=True)
        self.telemetry_thread.start()
        
    def stop_recording(self):
        """Detiene la grabación"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.log("⏹ Stopping recording...")
        
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except:
                if self.ffmpeg_process:
                    self.ffmpeg_process.kill()
            self.ffmpeg_process = None
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=3)
            
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            self.telemetry_thread.join(timeout=3)
        
        # Save telemetry
        if self.telemetry_data and self.current_session_dir:
            telemetry_file = self.current_session_dir / "telemetry.json"
            with open(telemetry_file, 'w', encoding='utf-8') as f:
                json.dump(self.telemetry_data, f, indent=2, ensure_ascii=False)
            self.log(f"✓ Telemetry saved: {len(self.telemetry_data)} records")
        
        duration = (datetime.now() - self.recording_start_time).total_seconds()
        self.log(f"✓ Recording completed ({duration:.0f}s)")
        self.log(f"📁 Files saved in: {self.current_session_dir}")
        
        self.status_indicator.set_color("#F59E0B")
        self.status_text.setText("System Monitoring")
        self.card_session.set_value("—")
        
        self.refresh_recordings()
        
    def record_screen(self):
        """Graba la pantalla"""
        video_file = self.current_session_dir / "race_recording.mp4"
        
        fps = self.fps_combo.currentText()
        crf = self.crf_combo.currentText()
        preset = self.preset_combo.currentText()
        
        # Platform-specific screen capture
        import platform
        system = platform.system()
        
        if system == "Windows":
            ffmpeg_cmd = [
                'ffmpeg', '-f', 'gdigrab', '-framerate', fps,
                '-i', 'desktop', '-c:v', 'libx264',
                '-preset', preset, '-crf', crf,
                '-pix_fmt', 'yuv420p', str(video_file)
            ]
        elif system == "Darwin":  # macOS
            ffmpeg_cmd = [
                'ffmpeg', '-f', 'avfoundation',
                '-framerate', fps, '-i', '1:0',
                '-c:v', 'libx264', '-preset', preset,
                '-crf', crf, '-pix_fmt', 'yuv420p',
                str(video_file)
            ]
        else:  # Linux
            ffmpeg_cmd = [
                'ffmpeg', '-f', 'x11grab',
                '-framerate', fps, '-i', ':0.0',
                '-c:v', 'libx264', '-preset', preset,
                '-crf', crf, '-pix_fmt', 'yuv420p',
                str(video_file)
            ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.log("🎥 Screen recording started")
            self.ffmpeg_process.wait()
            
        except FileNotFoundError:
            self.log("❌ ERROR: FFmpeg not found")
        except Exception as e:
            self.log(f"❌ Error in screen recording: {str(e)}")
            
    def record_telemetry(self):
        """Captura telemetría"""
        try:
            from acc_telemetry import ACCTelemetry
            
            acc_telemetry = ACCTelemetry()
            second_counter = 0
            interval = float(self.interval_combo.currentText())
            
            self.log("📊 Telemetry capture started")
            
            while self.is_recording:
                try:
                    if acc_telemetry.connect():
                        session_data = acc_telemetry.get_session_info()
                        standings = acc_telemetry.get_standings()
                        player_data = acc_telemetry.get_player_telemetry()
                        
                        record = {
                            'second': second_counter,
                            'timestamp': datetime.now().isoformat(),
                            'session': session_data,
                            'standings': standings,
                            'player_telemetry': player_data
                        }
                        
                        self.telemetry_data.append(record)
                        second_counter += 1
                        
                except Exception as e:
                    self.log(f"Error in telemetry: {str(e)}")
                
                time.sleep(interval)
            
            acc_telemetry.disconnect()
            
        except ImportError:
            self.log("⚠ acc_telemetry module not found")
        
    # ==================== MÉTODOS DE GRABACIONES ====================
    
    def refresh_recordings(self):
        """Actualiza la lista de grabaciones"""
        self.recordings_tree.clear()
        
        if not self.output_dir.exists():
            return
        
        sessions = sorted(
            [d for d in self.output_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for session_dir in sessions:
            video_file = session_dir / "race_recording.mp4"
            json_file = session_dir / "telemetry.json"
            
            if video_file.exists():
                stat = video_file.stat()
                date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                size_mb = stat.st_size / (1024 * 1024)
                
                # Calculate duration from JSON
                duration = "—"
                if json_file.exists():
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                            if data:
                                seconds = data[-1]['second']
                                mins = seconds // 60
                                secs = seconds % 60
                                duration = f"{mins:02d}:{secs:02d}"
                    except:
                        pass
                
                item = QTreeWidgetItem([
                    session_dir.name,
                    date,
                    duration,
                    f"{size_mb:.1f} MB"
                ])
                item.setData(0, Qt.UserRole, str(session_dir))
                self.recordings_tree.addTopLevelItem(item)
        
        self.log(f"Recordings refreshed: {len(sessions)} sessions found")
        
    def open_recordings_folder(self):
        """Abre la carpeta de grabaciones"""
        import platform
        system = platform.system()
        
        if system == "Windows":
            os.startfile(self.output_dir)
        elif system == "Darwin":  # macOS
            subprocess.run(['open', str(self.output_dir)])
        else:  # Linux
            subprocess.run(['xdg-open', str(self.output_dir)])
        
    def play_selected_video(self):
        """Reproduce el video seleccionado"""
        current_item = self.recordings_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a recording first")
            return
        
        session_path = Path(current_item.data(0, Qt.UserRole))
        video_file = session_path / "race_recording.mp4"
        
        if video_file.exists():
            import platform
            system = platform.system()
            
            if system == "Windows":
                os.startfile(video_file)
            elif system == "Darwin":
                subprocess.run(['open', str(video_file)])
            else:
                subprocess.run(['xdg-open', str(video_file)])
        else:
            QMessageBox.critical(self, "Error", "Video file not found")
        
    def view_selected_telemetry(self):
        """Visualiza la telemetría seleccionada"""
        current_item = self.recordings_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a recording first")
            return
        
        session_path = Path(current_item.data(0, Qt.UserRole))
        json_file = session_path / "telemetry.json"
        
        if json_file.exists():
            self.load_telemetry_file(json_file)
            self.switch_page(2)  # Switch to analytics page
        else:
            QMessageBox.critical(self, "Error", "Telemetry file not found")
        
    def open_selected_folder(self):
        """Abre la carpeta de la sesión seleccionada"""
        current_item = self.recordings_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a recording first")
            return
        
        session_path = Path(current_item.data(0, Qt.UserRole))
        
        import platform
        system = platform.system()
        
        if system == "Windows":
            os.startfile(session_path)
        elif system == "Darwin":
            subprocess.run(['open', str(session_path)])
        else:
            subprocess.run(['xdg-open', str(session_path)])
    
    # ==================== MÉTODOS DEL VISUALIZADOR ====================
    
    def load_telemetry_json(self):
        """Carga un archivo JSON de telemetría"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select telemetry file",
            str(self.output_dir),
            "JSON files (*.json);;All files (*.*)"
        )
        
        if filename:
            self.load_telemetry_file(Path(filename))
    
    def load_telemetry_file(self, filepath):
        """Carga y analiza un archivo de telemetría"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.telemetry_info.setText(
                f"✓ Loaded: {filepath.name} ({len(data)} records)"
            )
            self.telemetry_info.setStyleSheet("color: #10B981; font-size: 14px; font-weight: 500;")
            
            self.generate_telemetry_stats(data)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file:\n{str(e)}")
    
    def generate_telemetry_stats(self, data):
        """Genera estadísticas de la telemetría"""
        stats = "=" * 70 + "\n"
        stats += "TELEMETRY STATISTICS\n"
        stats += "=" * 70 + "\n\n"
        
        stats += f"📊 Total records: {len(data)}\n"
        
        if data:
            duration = data[-1]['second']
            stats += f"⏱️  Duration: {duration // 60:02d}:{duration % 60:02d}\n\n"
            
            # Speed analysis
            speeds = [r['player_telemetry']['speed_kmh'] for r in data 
                     if r.get('player_telemetry') and 'speed_kmh' in r['player_telemetry']]
            if speeds:
                stats += f"🏎️  Max speed: {max(speeds):.1f} km/h\n"
                stats += f"📈 Avg speed: {sum(speeds)/len(speeds):.1f} km/h\n\n"
            
            # Wheel locks analysis
            total_locks = 0
            lock_moments = []
            for i, r in enumerate(data):
                if r.get('player_telemetry') and r['player_telemetry'].get('tyres'):
                    locks = r['player_telemetry']['tyres'].get('locked', {})
                    count = sum(1 for v in locks.values() if v)
                    if count > 0:
                        total_locks += count
                        lock_moments.append((i, count))
            
            stats += f"🔴 Total wheel locks detected: {total_locks}\n"
            stats += f"⚠️  Moments with locks: {len(lock_moments)}\n\n"
            
            if lock_moments:
                stats += "First 10 locks:\n"
                for i, (second, count) in enumerate(lock_moments[:10]):
                    stats += f"  {second:4d}s - {count} wheel(s) locked\n"
                stats += "\n"
            
            # G-forces analysis
            g_lats = [r['player_telemetry'].get('g_force', {}).get('lateral', 0) 
                     for r in data if r.get('player_telemetry')]
            g_longs = [r['player_telemetry'].get('g_force', {}).get('longitudinal', 0) 
                      for r in data if r.get('player_telemetry')]
            
            if g_lats:
                stats += f"💨 Max lateral G: {max(abs(g) for g in g_lats):.2f} G\n"
            if g_longs:
                stats += f"🛑 Max braking G: {min(g_longs):.2f} G\n"
                stats += f"🚀 Max acceleration G: {max(g_longs):.2f} G\n\n"
            
            # Brake temperatures
            brake_temps = []
            for r in data:
                if r.get('player_telemetry') and r['player_telemetry'].get('brakes'):
                    temps = r['player_telemetry']['brakes']['temperature']
                    brake_temps.append(max(temps.values()))
            
            if brake_temps:
                stats += f"🔥 Max brake temp: {max(brake_temps):.0f}°C\n"
                stats += f"🌡️  Avg brake temp: {sum(brake_temps)/len(brake_temps):.0f}°C\n"
        
        stats += "\n" + "=" * 70 + "\n"
        stats += "💡 Use 'Web Viewer' button for detailed interactive charts\n"
        
        self.stats_text.setPlainText(stats)
    
    def open_web_viewer(self):
        """Abre el visualizador web"""
        viewer_path = Path(__file__).parent / "telemetry_viewer.html"
        if viewer_path.exists():
            webbrowser.open(viewer_path.as_uri())
        else:
            QMessageBox.critical(self, "Error", "Web viewer not found")
    
    # ==================== MÉTODOS DE CONFIGURACIÓN ====================
    
    def change_output_dir(self):
        """Cambia el directorio de salida"""
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "Select output directory",
            str(self.output_dir)
        )
        
        if new_dir:
            self.output_dir = Path(new_dir)
            self.output_dir_label.setText(str(self.output_dir))
            self.output_dir.mkdir(exist_ok=True)
            self.log(f"Output directory changed to: {self.output_dir}")
    
    def save_config(self):
        """Guarda la configuración"""
        self.fps_var = self.fps_combo.currentText()
        self.crf_var = self.crf_combo.currentText()
        self.preset_var = self.preset_combo.currentText()
        self.interval_var = self.interval_combo.currentText()
        
        # Save to config file
        config = {
            'fps': self.fps_var,
            'crf': self.crf_var,
            'preset': self.preset_var,
            'interval': self.interval_var,
            'output_dir': str(self.output_dir)
        }
        
        config_file = Path(__file__).parent / "config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.log("✓ Configuration saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save configuration:\n{str(e)}")
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def log(self, message):
        """Añade mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}]  {message}")
    
    def update_duration(self):
        """Actualiza el contador de duración"""
        if self.is_recording and self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.card_duration.set_value(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.card_records.set_value(str(len(self.telemetry_data)))

def main():
    app = QApplication(sys.argv)
    
    # Configurar fuente global
    font = QFont("SF Pro Display", 10)
    if font.family() != "SF Pro Display":
        font = QFont("Segoe UI", 10)  # Fallback para Windows
    app.setFont(font)
    
    window = ACCRecorderModern()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
