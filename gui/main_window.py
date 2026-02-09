"""
Ventana principal de la aplicación
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QFrame, QStackedWidget, QLineEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from pathlib import Path
from datetime import datetime
import threading
import time

from gui.widgets import SidebarButton
from gui.tabs import ControlTab, SessionsTab, AnalyticsTab, SettingsTab
from gui.styles import COLORS, SIDEBAR_STYLE, SEARCH_INPUT_STYLE

try:
    import psutil
except ImportError:
    psutil = None


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        
        # Estado de la aplicación
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
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup
        self.setWindowTitle("ACC Race Recorder")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        
        # Timer para actualizar duración
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)
        self.timer.start(1000)
        
    def setup_ui(self):
        """Configura la interfaz"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Contenido
        content = self.create_content_area()
        main_layout.addWidget(content, stretch=1)
        
        central.setLayout(main_layout)
        
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS['bg_primary']}; }}")
        
    def create_sidebar(self) -> QFrame:
        """Crea la barra lateral"""
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(SIDEBAR_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self.create_sidebar_header()
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
        
        for btn in self.nav_buttons:
            nav_layout.addWidget(btn)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
        
        # Footer
        version = QLabel("VERSION 1.0.1")
        version.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px; padding: 20px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        sidebar.setLayout(layout)
        return sidebar
        
    def create_sidebar_header(self) -> QFrame:
        """Crea el header del sidebar"""
        header = QFrame()
        header.setStyleSheet(f"background-color: white; border-bottom: 1px solid {COLORS['border']};")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 24, 20, 24)
        
        avatar = QLabel("👤")
        avatar.setStyleSheet(f"""
            font-size: 32px;
            background-color: {COLORS['bg_light']};
            border-radius: 32px;
            padding: 16px;
        """)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(64, 64)
        
        title = QLabel("ACC\nRECORDER")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 700; margin-top: 12px;")
        title.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(avatar, alignment=Qt.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        header.setLayout(layout)
        return header
        
    def create_content_area(self) -> QFrame:
        """Crea el área de contenido"""
        container = QFrame()
        container.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Pages
        self.pages = QStackedWidget()
        
        # Crear pestañas
        self.control_tab = ControlTab()
        self.sessions_tab = SessionsTab(self.output_dir)
        self.analytics_tab = AnalyticsTab(self.output_dir)
        self.settings_tab = SettingsTab(self.output_dir)
        
        # Conectar señales
        self.control_tab.start_monitoring_requested.connect(self.start_monitoring)
        self.control_tab.stop_monitoring_requested.connect(self.stop_monitoring)
        self.sessions_tab.switch_to_analytics.connect(self.load_analytics_file)
        self.settings_tab.config_saved.connect(self.on_config_saved)
        
        self.pages.addWidget(self.control_tab)
        self.pages.addWidget(self.sessions_tab)
        self.pages.addWidget(self.analytics_tab)
        self.pages.addWidget(self.settings_tab)
        
        layout.addWidget(self.pages)
        
        container.setLayout(layout)
        return container
        
    def create_header(self) -> QFrame:
        """Crea el header con búsqueda"""
        header = QFrame()
        header.setStyleSheet("background-color: transparent;")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.page_title = QLabel("System Status")
        self.page_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700;")
        
        layout.addWidget(self.page_title)
        layout.addStretch()
        
        # Search bar
        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        search_container.setFixedWidth(300)
        
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 8, 12, 8)
        
        search_icon = QLabel("🔍")
        search_input = QLineEdit()
        search_input.setPlaceholderText("Find here...")
        search_input.setStyleSheet(SEARCH_INPUT_STYLE)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(search_input)
        search_container.setLayout(search_layout)
        
        layout.addWidget(search_container)
        
        header.setLayout(layout)
        return header
        
    def switch_page(self, index: int):
        """Cambia de página"""
        self.pages.setCurrentIndex(index)
        
        titles = ["System Status", "Recorded Sessions", "Telemetry Analytics", "System Settings"]
        self.page_title.setText(titles[index])
        
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            
    def load_analytics_file(self, filepath: Path):
        """Carga un archivo en analytics y cambia de pestaña"""
        self.analytics_tab.load_file(filepath)
        self.switch_page(2)
        
    def on_config_saved(self, config: dict):
        """Callback cuando se guarda la configuración"""
        self.output_dir = Path(config['output_dir'])
        self.control_tab.log("✓ Configuration updated")
        
    # ========== Métodos de control ==========
    
    def start_monitoring(self):
        """Inicia el monitoreo"""
        self.is_monitoring = True
        self.control_tab.set_monitoring_active(True)
        self.control_tab.set_status("System Monitoring", COLORS['status_monitoring'])
        self.control_tab.log("✓ Monitoring started - Waiting for ACC...")
        
        self.monitor_thread = threading.Thread(target=self.monitor_acc, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_monitoring = False
        
        if self.is_recording:
            self.stop_recording()
            
        self.control_tab.set_monitoring_active(False)
        self.control_tab.set_status("System Offline", COLORS['status_offline'])
        self.control_tab.log("✗ Monitoring stopped")
        
    def monitor_acc(self):
        """Monitorea el proceso ACC"""
        self.control_tab.log("ACC monitoring thread started...")
        
        if not psutil:
            self.control_tab.log("⚠ psutil not installed - cannot monitor ACC")
            return
        
        while self.is_monitoring:
            try:
                acc_running = self.is_acc_running()
                
                if acc_running and not self.is_recording:
                    self.control_tab.log("⚑ ACC detected - Starting recording")
                    self.start_recording()
                elif not acc_running and self.is_recording:
                    self.control_tab.log("ACC closed - Stopping recording")
                    self.stop_recording()
                    
            except Exception as e:
                self.control_tab.log(f"Error: {str(e)}")
            
            time.sleep(2)
        
    def is_acc_running(self) -> bool:
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
        
        self.control_tab.set_status("Recording Active", COLORS['status_recording'])
        self.control_tab.update_session_name(session_name)
        self.control_tab.log(f"🔴 Recording started: {session_name}")
        
        self.telemetry_data = []
        
    def stop_recording(self):
        """Detiene la grabación"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.control_tab.log("⏹ Stopping recording...")
        
        # Guardar telemetría
        if self.telemetry_data and self.current_session_dir:
            import json
            telemetry_file = self.current_session_dir / "telemetry.json"
            with open(telemetry_file, 'w', encoding='utf-8') as f:
                json.dump(self.telemetry_data, f, indent=2, ensure_ascii=False)
            self.control_tab.log(f"✓ Telemetry saved: {len(self.telemetry_data)} records")
        
        duration = (datetime.now() - self.recording_start_time).total_seconds()
        self.control_tab.log(f"✓ Recording completed ({duration:.0f}s)")
        
        self.control_tab.set_status("System Monitoring", COLORS['status_monitoring'])
        self.control_tab.update_session_name("—")
        
        self.sessions_tab.refresh_recordings()
        
    def update_duration(self):
        """Actualiza el contador de duración"""
        if self.is_recording and self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            
            self.control_tab.update_duration(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.control_tab.update_records(len(self.telemetry_data))
