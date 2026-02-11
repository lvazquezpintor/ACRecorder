"""
Ventana principal de la aplicación
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QFrame, QStackedWidget, QLineEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from pathlib import Path
from datetime import datetime
import sys
import os

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.widgets import SidebarButton
from gui.tabs import ControlTab, SessionsTab, AnalyticsTab, SettingsTab
from gui.styles import COLORS, SIDEBAR_STYLE, SEARCH_INPUT_STYLE
from core import TelemetryRecorder, ScreenRecorder, ACCSessionMonitor, SessionStatus
from acc_telemetry import ACCTelemetry


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        
        # Estado de la aplicación
        self.is_monitoring = False
        self.output_dir = Path.home() / "ACC_Recordings"
        self.output_dir.mkdir(exist_ok=True)
        
        # Inicializar telemetría de ACC
        self.acc_telemetry = ACCTelemetry()
        
        # Inicializar grabadores
        self.telemetry_recorder = TelemetryRecorder(self.output_dir)
        self.screen_recorder = ScreenRecorder(self.output_dir)
        
        # Inicializar monitor de sesiones
        self.session_monitor = ACCSessionMonitor(self.acc_telemetry)
        
        # Configurar callbacks de telemetría
        self.telemetry_recorder.on_recording_started = self._on_telemetry_started
        self.telemetry_recorder.on_recording_stopped = self._on_telemetry_stopped
        self.telemetry_recorder.on_telemetry_update = self._on_telemetry_update
        
        # Configurar callbacks de grabación de pantalla
        self.screen_recorder.on_recording_started = self._on_screen_started
        self.screen_recorder.on_recording_stopped = self._on_screen_stopped
        self.screen_recorder.on_error = self._on_screen_error
        
        # Configurar callbacks del monitor de sesiones
        self.session_monitor.on_race_started = self._on_race_started
        self.session_monitor.on_race_ended = self._on_race_ended
        self.session_monitor.on_status_changed = self._on_status_changed
        
        # Setup
        self.setWindowTitle("ACC Race Recorder")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        
        # Timer para actualizar duración y telemetría
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
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
        version = QLabel("VERSION 1.0.2")
        version.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px; padding: 20px; background: transparent; border: none;")
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
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 700; margin-top: 12px; background: transparent; border: none;")
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
        self.page_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        
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
        search_icon.setStyleSheet("background: transparent; border: none;")
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
        
        # Actualizar directorios de los grabadores
        self.telemetry_recorder.output_dir = self.output_dir
        self.screen_recorder.output_dir = self.output_dir
        
        # Actualizar configuración de screen recorder si existe
        if 'screen_recorder' in config:
            self.screen_recorder.configure(**config['screen_recorder'])
        
        self.control_tab.log("✓ Configuration updated")
        
    # ========== Métodos de control ==========
    
    def start_monitoring(self):
        """Inicia el monitoreo de sesiones de ACC"""
        self.is_monitoring = True
        self.control_tab.set_monitoring_active(True)
        self.control_tab.set_status("Waiting for Race", COLORS['status_monitoring'])
        self.control_tab.log("✓ Monitoring started - Waiting for ACC race to begin...")
        
        # Iniciar monitor de sesiones
        if self.session_monitor.start_monitoring():
            self.control_tab.log("✓ Connected to ACC telemetry")
        else:
            self.control_tab.log("⚠ Could not connect to ACC - Make sure the game is running")
        
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_monitoring = False
        
        # Detener grabación si está activa
        if self.telemetry_recorder.is_recording:
            self.stop_recording()
        
        # Detener monitor de sesiones
        self.session_monitor.stop_monitoring()
        
        self.control_tab.set_monitoring_active(False)
        self.control_tab.set_status("System Offline", COLORS['status_offline'])
        self.control_tab.log("✗ Monitoring stopped")
        
    def start_recording(self, race_data: dict):
        """
        Inicia la grabación cuando comienza una carrera
        
        Args:
            race_data: Información sobre la carrera que comienza
        """
        try:
            # Crear nombre de sesión basado en tipo de sesión
            session_type = race_data.get('session_type', 'Race')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"ACC_{session_type}_{timestamp}"
            
            # Iniciar grabación de telemetría
            session_dir = self.telemetry_recorder.start_recording(session_name)
            
            # Iniciar grabación de pantalla
            video_filename = f"{session_name}.mp4"
            self.screen_recorder.start_recording(video_filename)
            
            self.control_tab.set_status("Recording Active", COLORS['status_recording'])
            self.control_tab.update_session_name(f"{session_type} - {timestamp}")
            
        except Exception as e:
            self.control_tab.log(f"❌ Error starting recording: {str(e)}")
        
    def stop_recording(self):
        """Detiene la grabación cuando termina la carrera"""
        if not self.telemetry_recorder.is_recording:
            return
            
        self.control_tab.log("⏹ Stopping recording...")
        
        # Detener grabación de pantalla
        try:
            self.screen_recorder.stop_recording()
        except Exception as e:
            self.control_tab.log(f"⚠ Error stopping screen recording: {str(e)}")
        
        # Detener grabación de telemetría
        try:
            self.telemetry_recorder.stop_recording()
        except Exception as e:
            self.control_tab.log(f"⚠ Error stopping telemetry recording: {str(e)}")
        
        self.control_tab.set_status("Waiting for Race", COLORS['status_monitoring'])
        self.control_tab.update_session_name("—")
        
        self.sessions_tab.refresh_recordings()
        
    def update_ui(self):
        """Actualiza la UI periódicamente"""
        # Actualizar duración si está grabando
        if self.telemetry_recorder.is_recording:
            stats = self.telemetry_recorder.get_current_stats()
            
            elapsed = stats['duration']
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            self.control_tab.update_duration(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.control_tab.update_records(stats['records_count'])
        
        # Capturar telemetría si está en carrera
        if self.session_monitor.is_in_race and self.telemetry_recorder.is_recording:
            self._capture_telemetry()
    
    def _capture_telemetry(self):
        """Captura y guarda datos de telemetría"""
        try:
            # Obtener datos del jugador
            player_data = self.acc_telemetry.get_player_telemetry()
            if player_data:
                self.telemetry_recorder.add_telemetry_record(player_data)
            
            # Obtener info de sesión
            session_info = self.acc_telemetry.get_session_info()
            if session_info:
                # Añadir info de sesión al último registro
                combined_data = {**player_data, **session_info}
                # No necesitamos añadirlo de nuevo, solo actualizar
        except Exception as e:
            pass  # Silenciar errores de captura individual
    
    # ========== Callbacks del monitor de sesiones ==========
    
    def _on_race_started(self, race_data: dict):
        """Callback cuando comienza una carrera"""
        session_type = race_data.get('session_type', 'Unknown')
        self.control_tab.log(f"🏁 Race started: {session_type}")
        self.start_recording(race_data)
    
    def _on_race_ended(self, race_data: dict):
        """Callback cuando termina una carrera"""
        duration = race_data.get('duration_seconds', 0)
        self.control_tab.log(f"🏁 Race ended - Duration: {duration:.0f}s")
        self.stop_recording()
    
    def _on_status_changed(self, old_status: SessionStatus, new_status: SessionStatus):
        """Callback cuando cambia el estado de la sesión"""
        status_messages = {
            SessionStatus.OFF: ("ACC Disconnected", COLORS['status_offline']),
            SessionStatus.MENU: ("In Menus", COLORS['status_monitoring']),
            SessionStatus.REPLAY: ("Watching Replay", COLORS['status_monitoring']),
            SessionStatus.LIVE_PAUSED: ("Session Paused", COLORS['status_monitoring']),
            SessionStatus.LIVE_WAITING: ("In Pits", COLORS['status_monitoring']),
            SessionStatus.LIVE_RACING: ("Racing", COLORS['status_recording'])
        }
        
        if new_status in status_messages:
            msg, color = status_messages[new_status]
            if not self.telemetry_recorder.is_recording:
                self.control_tab.set_status(msg, color)
    
    # ========== Callbacks de grabadores ==========
    
    def _on_telemetry_started(self, session_name: str):
        """Callback cuando inicia la grabación de telemetría"""
        self.control_tab.log(f"🔴 Telemetry recording started: {session_name}")
    
    def _on_telemetry_stopped(self, records_count: int, duration: float):
        """Callback cuando finaliza la grabación de telemetría"""
        self.control_tab.log(f"✓ Telemetry saved: {records_count} records ({duration:.0f}s)")
    
    def _on_telemetry_update(self, data: dict):
        """Callback cuando se actualiza la telemetría"""
        # Aquí se podría actualizar UI en tiempo real si se necesita
        pass
    
    def _on_screen_started(self, output_file: str):
        """Callback cuando inicia la grabación de pantalla"""
        self.control_tab.log(f"🎥 Screen recording started: {Path(output_file).name}")
    
    def _on_screen_stopped(self, duration: float):
        """Callback cuando finaliza la grabación de pantalla"""
        self.control_tab.log(f"✓ Screen recording completed ({duration:.0f}s)")
    
    def _on_screen_error(self, error_msg: str):
        """Callback cuando hay un error en la grabación de pantalla"""
        self.control_tab.log(f"❌ Screen recorder error: {error_msg}")
