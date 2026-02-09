"""
Pestaña de Analytics - Visualización de telemetría
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QTextEdit, QFileDialog, QMessageBox)
from PySide6.QtCore import Signal
from pathlib import Path
import json
import webbrowser

from gui.widgets import ModernButton
from gui.styles import COLORS, PANEL_STYLE, PANEL_TITLE_STYLE, TEXT_EDIT_STYLE


class AnalyticsTab(QWidget):
    """Pestaña de análisis de telemetría"""
    
    def __init__(self, output_dir: Path):
        super().__init__()
        self.output_dir = output_dir
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
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
        self.telemetry_info.setStyleSheet("color: #718096; font-size: 14px; background: transparent; border: none;")
        layout.addWidget(self.telemetry_info)
        
        # Stats panel
        stats_panel = self.create_stats_panel()
        layout.addWidget(stats_panel, stretch=1)
        
        self.setLayout(layout)
        
    def create_stats_panel(self) -> QFrame:
        """Crea el panel de estadísticas"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        title = QLabel("Quick Stats")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet(TEXT_EDIT_STYLE)
        
        layout.addWidget(title)
        layout.addWidget(self.stats_text)
        
        panel.setLayout(layout)
        return panel
        
    def load_telemetry_json(self):
        """Carga un archivo JSON"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select telemetry file",
            str(self.output_dir),
            "JSON files (*.json);;All files (*.*)"
        )
        
        if filename:
            self.load_file(Path(filename))
    
    def load_file(self, filepath: Path):
        """Carga y analiza un archivo de telemetría"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.telemetry_info.setText(f"✓ Loaded: {filepath.name} ({len(data)} records)")
            self.telemetry_info.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 14px; font-weight: 500; background: transparent; border: none;")
            
            self.generate_stats(data)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file:\n{str(e)}")
    
    def generate_stats(self, data: list):
        """Genera estadísticas básicas"""
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
                stats += f"📈 Avg speed: {sum(speeds)/len(speeds):.1f} km/h\n"
        
        stats += "\n" + "=" * 70 + "\n"
        stats += "💡 Use 'Web Viewer' for detailed charts\n"
        
        self.stats_text.setPlainText(stats)
    
    def open_web_viewer(self):
        """Abre el visualizador web"""
        viewer_path = Path(__file__).parent.parent.parent / "telemetry_viewer.html"
        if viewer_path.exists():
            webbrowser.open(viewer_path.as_uri())
        else:
            QMessageBox.critical(self, "Error", "Web viewer not found")
