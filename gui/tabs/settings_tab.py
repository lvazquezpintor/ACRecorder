"""
Pestaña de Settings - Configuración
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QComboBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Signal
from pathlib import Path
import json

from gui.widgets import ModernButton
from gui.styles import COLORS, PANEL_STYLE, PANEL_TITLE_STYLE, COMBO_BOX_STYLE


class SettingsTab(QWidget):
    """Pestaña de configuración"""
    
    # Señal cuando se guarda la configuración
    config_saved = Signal(dict)
    
    def __init__(self, output_dir: Path):
        super().__init__()
        self.output_dir = output_dir
        
        # Valores por defecto
        self.fps_var = "30"
        self.crf_var = "23"
        self.preset_var = "ultrafast"
        self.interval_var = "1"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Video settings
        video_panel = self.create_video_panel()
        layout.addWidget(video_panel)
        
        # Telemetry settings
        telem_panel = self.create_telemetry_panel()
        layout.addWidget(telem_panel)
        
        # Output directory
        dir_panel = self.create_directory_panel()
        layout.addWidget(dir_panel)
        
        # Save button
        btn_save = ModernButton("💾  SAVE CONFIGURATION", success=True)
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
    def create_video_panel(self) -> QFrame:
        """Panel de configuración de video"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        title = QLabel("Video Recording")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(title)
        
        # FPS
        fps_row = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; min-width: 120px;")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(['24', '30', '60'])
        self.fps_combo.setCurrentText(self.fps_var)
        self.fps_combo.setStyleSheet(COMBO_BOX_STYLE)
        fps_row.addWidget(fps_label)
        fps_row.addWidget(self.fps_combo)
        fps_row.addStretch()
        layout.addLayout(fps_row)
        
        # CRF
        crf_row = QHBoxLayout()
        crf_label = QLabel("Quality (CRF):")
        crf_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; min-width: 120px;")
        self.crf_combo = QComboBox()
        self.crf_combo.addItems(['18', '23', '28'])
        self.crf_combo.setCurrentText(self.crf_var)
        self.crf_combo.setStyleSheet(COMBO_BOX_STYLE)
        crf_hint = QLabel("(18=High, 23=Medium, 28=Low)")
        crf_hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        crf_row.addWidget(crf_label)
        crf_row.addWidget(self.crf_combo)
        crf_row.addWidget(crf_hint)
        crf_row.addStretch()
        layout.addLayout(crf_row)
        
        # Preset
        preset_row = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; min-width: 120px;")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['ultrafast', 'fast', 'medium'])
        self.preset_combo.setCurrentText(self.preset_var)
        self.preset_combo.setStyleSheet(COMBO_BOX_STYLE)
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.preset_combo)
        preset_row.addStretch()
        layout.addLayout(preset_row)
        
        panel.setLayout(layout)
        return panel
        
    def create_telemetry_panel(self) -> QFrame:
        """Panel de configuración de telemetría"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        title = QLabel("Telemetry Capture")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(title)
        
        interval_row = QHBoxLayout()
        interval_label = QLabel("Interval (sec):")
        interval_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; min-width: 120px;")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['0.5', '1', '2'])
        self.interval_combo.setCurrentText(self.interval_var)
        self.interval_combo.setStyleSheet(COMBO_BOX_STYLE)
        interval_row.addWidget(interval_label)
        interval_row.addWidget(self.interval_combo)
        interval_row.addStretch()
        layout.addLayout(interval_row)
        
        panel.setLayout(layout)
        return panel
        
    def create_directory_panel(self) -> QFrame:
        """Panel de directorio de salida"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        title = QLabel("Output Directory")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(title)
        
        dir_row = QHBoxLayout()
        self.output_dir_label = QLabel(str(self.output_dir))
        self.output_dir_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        btn_change = ModernButton("Change")
        btn_change.clicked.connect(self.change_output_dir)
        dir_row.addWidget(self.output_dir_label)
        dir_row.addWidget(btn_change)
        layout.addLayout(dir_row)
        
        panel.setLayout(layout)
        return panel
        
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
    
    def save_config(self):
        """Guarda la configuración"""
        config = {
            'fps': self.fps_combo.currentText(),
            'crf': self.crf_combo.currentText(),
            'preset': self.preset_combo.currentText(),
            'interval': self.interval_combo.currentText(),
            'output_dir': str(self.output_dir)
        }
        
        config_file = Path(__file__).parent.parent.parent / "config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.config_saved.emit(config)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save:\n{str(e)}")
    
    def get_config(self) -> dict:
        """Obtiene la configuración actual"""
        return {
            'fps': self.fps_combo.currentText(),
            'crf': self.crf_combo.currentText(),
            'preset': self.preset_combo.currentText(),
            'interval': self.interval_combo.currentText(),
            'output_dir': self.output_dir
        }
