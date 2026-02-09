"""
Pestaña de Sessions - Grabaciones guardadas
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                               QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import platform

from gui.widgets import ModernButton
from gui.styles import PANEL_STYLE, TREE_WIDGET_STYLE


class SessionsTab(QWidget):
    """Pestaña de sesiones grabadas"""
    
    # Señal para cambiar a la pestaña de analytics
    switch_to_analytics = Signal(object)  # Path del archivo JSON
    
    def __init__(self, output_dir: Path):
        super().__init__()
        self.output_dir = output_dir
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Botones superiores
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
        list_panel = self.create_recordings_list()
        layout.addWidget(list_panel, stretch=1)
        
        # Botones de acción
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
        
        self.setLayout(layout)
        
        # Cargar grabaciones iniciales
        self.refresh_recordings()
        
    def create_recordings_list(self) -> QFrame:
        """Crea el panel con la lista de grabaciones"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # TreeWidget
        self.recordings_tree = QTreeWidget()
        self.recordings_tree.setHeaderLabels(['Session', 'Date', 'Duration', 'Size'])
        self.recordings_tree.setStyleSheet(TREE_WIDGET_STYLE)
        
        # Configurar columnas
        header = self.recordings_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.recordings_tree)
        panel.setLayout(layout)
        return panel
        
    # ========== Métodos de acción ==========
    
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
                
                # Calcular duración del JSON
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
        
    def open_recordings_folder(self):
        """Abre la carpeta de grabaciones"""
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
            # Emitir señal para cambiar de pestaña
            self.switch_to_analytics.emit(json_file)
        else:
            QMessageBox.critical(self, "Error", "Telemetry file not found")
        
    def open_selected_folder(self):
        """Abre la carpeta de la sesión seleccionada"""
        current_item = self.recordings_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a recording first")
            return
        
        session_path = Path(current_item.data(0, Qt.UserRole))
        system = platform.system()
        
        if system == "Windows":
            os.startfile(session_path)
        elif system == "Darwin":
            subprocess.run(['open', str(session_path)])
        else:
            subprocess.run(['xdg-open', str(session_path)])
