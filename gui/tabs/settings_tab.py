"""
Pestaña de Settings - Configuración
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QComboBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Signal
from pathlib import Path
import json

from gui.widgets import ModernButton
from gui.styles import COLORS, PANEL_STYLE, PANEL_TITLE_STYLE, COMBO_BOX_STYLE, SETTING_LABEL_STYLE, HINT_LABEL_STYLE


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
        
        # Codec / Hardware Acceleration
        codec_row = QHBoxLayout()
        codec_label = QLabel("Codec:")
        codec_label.setStyleSheet(SETTING_LABEL_STYLE)
        codec_label.setMinimumWidth(120)
        self.codec_combo = QComboBox()
        self.codec_combo.addItems([
            'Auto (Detect GPU)',
            'NVIDIA NVENC (h264_nvenc)',
            'Intel QuickSync (h264_qsv)',
            'Apple VideoToolbox (macOS)',
            'Software (libx264)'
        ])
        self.codec_combo.setCurrentIndex(0)
        self.codec_combo.setStyleSheet(COMBO_BOX_STYLE)
        codec_row.addWidget(codec_label)
        codec_row.addWidget(self.codec_combo)
        codec_row.addStretch()
        layout.addLayout(codec_row)
        
        # FPS
        fps_row = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet(SETTING_LABEL_STYLE)
        fps_label.setMinimumWidth(120)
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
        crf_label.setStyleSheet(SETTING_LABEL_STYLE)
        crf_label.setMinimumWidth(120)
        self.crf_combo = QComboBox()
        self.crf_combo.addItems(['18', '23', '28'])
        self.crf_combo.setCurrentText(self.crf_var)
        self.crf_combo.setStyleSheet(COMBO_BOX_STYLE)
        crf_hint = QLabel("(18=High, 23=Medium, 28=Low)")
        crf_hint.setStyleSheet(HINT_LABEL_STYLE)
        crf_row.addWidget(crf_label)
        crf_row.addWidget(self.crf_combo)
        crf_row.addWidget(crf_hint)
        crf_row.addStretch()
        layout.addLayout(crf_row)
        
        # Preset
        preset_row = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_label.setStyleSheet(SETTING_LABEL_STYLE)
        preset_label.setMinimumWidth(120)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['ultrafast', 'fast', 'medium'])
        self.preset_combo.setCurrentText(self.preset_var)
        self.preset_combo.setStyleSheet(COMBO_BOX_STYLE)
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.preset_combo)
        preset_row.addStretch()
        layout.addLayout(preset_row)
        
        # Audio Device
        audio_row = QHBoxLayout()
        audio_label = QLabel("Audio Device:")
        audio_label.setStyleSheet(SETTING_LABEL_STYLE)
        audio_label.setMinimumWidth(120)
        self.audio_combo = QComboBox()
        self.audio_combo.addItem('Auto (System Default)')
        self.audio_combo.setStyleSheet(COMBO_BOX_STYLE)
        audio_row.addWidget(audio_label)
        audio_row.addWidget(self.audio_combo)
        audio_row.addStretch()
        layout.addLayout(audio_row)
        
        # Botón para refrescar dispositivos de audio
        refresh_btn = ModernButton("🔄  Refresh Audio Devices")
        refresh_btn.clicked.connect(self.refresh_audio_devices)
        layout.addWidget(refresh_btn)
        
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
        interval_label.setStyleSheet(SETTING_LABEL_STYLE)
        interval_label.setMinimumWidth(120)
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
        self.output_dir_label.setStyleSheet("color: #4A5568; font-size: 13px; background: transparent; border: none;")
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
    
    def refresh_audio_devices(self):
        """Refresca la lista de dispositivos de audio"""
        from core.screen_recorder import ScreenRecorder
        
        try:
            # Crear instancia temporal para obtener dispositivos
            temp_recorder = ScreenRecorder(self.output_dir)
            devices = temp_recorder.list_audio_devices()
            
            # Actualizar combo box
            current_selection = self.audio_combo.currentText()
            self.audio_combo.clear()
            self.audio_combo.addItem('Auto (System Default)')
            
            for device in devices:
                self.audio_combo.addItem(device)
            
            # Restaurar selección si existe
            index = self.audio_combo.findText(current_selection)
            if index >= 0:
                self.audio_combo.setCurrentIndex(index)
            
            QMessageBox.information(self, "Success", f"Found {len(devices)} audio devices")
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not refresh devices:\n{str(e)}")
    
    def save_config(self):
        """Guarda la configuración"""
        # Mapear codec seleccionado
        codec_map = {
            'Auto (Detect GPU)': None,
            'NVIDIA NVENC (h264_nvenc)': 'nvenc',
            'Intel QuickSync (h264_qsv)': 'qsv',
            'Apple VideoToolbox (macOS)': 'videotoolbox',
            'Software (libx264)': None
        }
        
        selected_codec = self.codec_combo.currentText()
        hw_accel = codec_map.get(selected_codec)
        
        # Dispositivo de audio seleccionado
        audio_device = None
        if self.audio_combo.currentText() != 'Auto (System Default)':
            audio_device = self.audio_combo.currentText()
        
        config = {
            'fps': self.fps_combo.currentText(),
            'crf': self.crf_combo.currentText(),
            'preset': self.preset_combo.currentText(),
            'interval': self.interval_combo.currentText(),
            'output_dir': str(self.output_dir),
            'hw_accel': hw_accel,
            'audio_device': audio_device
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
        # Mapear codec seleccionado
        codec_map = {
            'Auto (Detect GPU)': None,
            'NVIDIA NVENC (h264_nvenc)': 'nvenc',
            'Intel QuickSync (h264_qsv)': 'qsv',
            'Apple VideoToolbox (macOS)': 'videotoolbox',
            'Software (libx264)': None
        }
        
        selected_codec = self.codec_combo.currentText()
        hw_accel = codec_map.get(selected_codec)
        
        # Dispositivo de audio seleccionado
        audio_device = None
        if self.audio_combo.currentText() != 'Auto (System Default)':
            audio_device = self.audio_combo.currentText()
        
        return {
            'fps': self.fps_combo.currentText(),
            'crf': self.crf_combo.currentText(),
            'preset': self.preset_combo.currentText(),
            'interval': self.interval_combo.currentText(),
            'output_dir': self.output_dir,
            'hw_accel': hw_accel,
            'audio_device': audio_device
        }
