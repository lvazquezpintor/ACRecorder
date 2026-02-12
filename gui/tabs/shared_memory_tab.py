"""
Pestaña de Shared Memory - Visualización en tiempo real de TODOS los datos
Soporta múltiples simuladores de la familia Assetto Corsa
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QScrollArea, QComboBox, QGridLayout)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import struct
import mmap
from typing import Dict, Optional, Any

from gui.styles import COLORS, PANEL_STYLE, PANEL_TITLE_STYLE


class SharedMemoryTab(QWidget):
    """Pestaña para visualizar toda la shared memory en tiempo real"""
    
    SIMULATORS = {
        'ACC': {
            'physics': 'Local\\acpmf_physics',
            'graphics': 'Local\\acpmf_graphics',
            'static': 'Local\\acpmf_static',
            'size': 2048
        },
        'AC': {
            'physics': 'Local\\acpmf_physics',
            'graphics': 'Local\\acpmf_graphics',
            'static': 'Local\\acpmf_static',
            'size': 2048
        }
    }
    
    def __init__(self):
        super().__init__()
        
        self.physics_handle = None
        self.graphics_handle = None
        self.static_handle = None
        self.connected = False
        self.current_simulator = 'ACC'
        
        self.physics_labels = {}
        self.graphics_labels = {}
        self.static_labels = {}
        
        self.setup_ui()
        
        # Timer para actualización
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)  # 20Hz
        
    def setup_ui(self):
        """Configura la interfaz"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Header con selector de simulador
        header = self.create_header()
        layout.addWidget(header)
        
        # Panel con scroll para todos los datos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['bg_light']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['text_light']};
            }}
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # Crear paneles para cada tipo de memoria
        self.physics_panel = self.create_memory_panel("Physics Memory", self.physics_labels)
        self.graphics_panel = self.create_memory_panel("Graphics Memory", self.graphics_labels)
        self.static_panel = self.create_memory_panel("Static Memory", self.static_labels)
        
        content_layout.addWidget(self.physics_panel)
        content_layout.addWidget(self.graphics_panel)
        content_layout.addWidget(self.static_panel)
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
        
        # Intentar conectar
        self.connect_simulator()
    
    def create_header(self) -> QFrame:
        """Crea el header con selector de simulador"""
        header = QFrame()
        header.setStyleSheet(PANEL_STYLE)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 16, 24, 16)
        
        label = QLabel("Simulator:")
        label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 600;")
        
        self.simulator_combo = QComboBox()
        self.simulator_combo.addItems(['ACC', 'AC'])
        self.simulator_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        """)
        self.simulator_combo.currentTextChanged.connect(self.on_simulator_changed)
        
        self.connection_status = QLabel("● Disconnected")
        self.connection_status.setStyleSheet(f"color: {COLORS['status_offline']}; font-size: 13px; font-weight: 600;")
        
        layout.addWidget(label)
        layout.addWidget(self.simulator_combo)
        layout.addStretch()
        layout.addWidget(self.connection_status)
        
        header.setLayout(layout)
        return header
    
    def create_memory_panel(self, title: str, labels_dict: dict) -> QFrame:
        """Crea un panel para un tipo de memoria"""
        panel = QFrame()
        panel.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        # Título del panel
        title_label = QLabel(title)
        title_label.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(title_label)
        
        # Grid para los datos
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 8, 0, 0)
        
        labels_dict['grid'] = grid
        
        layout.addLayout(grid)
        panel.setLayout(layout)
        
        return panel
    
    def on_simulator_changed(self, simulator: str):
        """Cambia el simulador"""
        self.disconnect_simulator()
        self.current_simulator = simulator
        self.connect_simulator()
    
    def connect_simulator(self) -> bool:
        """Conecta con la memoria compartida del simulador"""
        try:
            config = self.SIMULATORS[self.current_simulator]
            size = config['size']
            
            self.physics_handle = mmap.mmap(-1, size, config['physics'])
            self.graphics_handle = mmap.mmap(-1, size, config['graphics'])
            self.static_handle = mmap.mmap(-1, size, config['static'])
            
            self.connected = True
            self.connection_status.setText(f"● Connected to {self.current_simulator}")
            self.connection_status.setStyleSheet(f"color: {COLORS['status_recording']}; font-size: 13px; font-weight: 600;")
            return True
            
        except Exception as e:
            self.connected = False
            self.connection_status.setText("● Disconnected")
            self.connection_status.setStyleSheet(f"color: {COLORS['status_offline']}; font-size: 13px; font-weight: 600;")
            return False
    
    def disconnect_simulator(self):
        """Desconecta de la memoria compartida"""
        if self.physics_handle:
            self.physics_handle.close()
        if self.graphics_handle:
            self.graphics_handle.close()
        if self.static_handle:
            self.static_handle.close()
        
        self.connected = False
        self.connection_status.setText("● Disconnected")
        self.connection_status.setStyleSheet(f"color: {COLORS['status_offline']}; font-size: 13px; font-weight: 600;")
    
    def update_data(self):
        """Actualiza los datos de la memoria compartida"""
        if not self.connected:
            self.connect_simulator()
            return
        
        try:
            # Leer y parsear cada tipo de memoria
            physics_data = self.read_and_parse_physics()
            graphics_data = self.read_and_parse_graphics()
            static_data = self.read_and_parse_static()
            
            # Actualizar UI
            self.update_panel(self.physics_labels, physics_data)
            self.update_panel(self.graphics_labels, graphics_data)
            self.update_panel(self.static_labels, static_data)
            
        except Exception as e:
            self.connected = False
            self.connection_status.setText(f"● Error: {str(e)[:30]}")
            self.connection_status.setStyleSheet(f"color: {COLORS['status_offline']}; font-size: 13px; font-weight: 600;")
    
    def read_and_parse_physics(self) -> Dict[str, Any]:
        """Lee y parsea datos de Physics"""
        if not self.physics_handle:
            return {}
        
        try:
            self.physics_handle.seek(0)
            data = self.physics_handle.read(2048)
            
            parsed = {}
            
            # Datos básicos
            parsed['packetId'] = struct.unpack('i', data[0:4])[0]
            parsed['gas'] = struct.unpack('f', data[4:8])[0]
            parsed['brake'] = struct.unpack('f', data[8:12])[0]
            parsed['fuel'] = struct.unpack('f', data[12:16])[0]
            parsed['gear'] = struct.unpack('i', data[16:20])[0]
            parsed['rpm'] = struct.unpack('i', data[20:24])[0]
            parsed['steerAngle'] = struct.unpack('f', data[24:28])[0]
            parsed['speedKmh'] = struct.unpack('f', data[28:32])[0]
            
            # Velocidad (vec3)
            parsed['velocity_x'] = struct.unpack('f', data[32:36])[0]
            parsed['velocity_y'] = struct.unpack('f', data[36:40])[0]
            parsed['velocity_z'] = struct.unpack('f', data[40:44])[0]
            
            # Aceleración G (vec3)
            parsed['accG_x'] = struct.unpack('f', data[44:48])[0]
            parsed['accG_y'] = struct.unpack('f', data[48:52])[0]
            parsed['accG_z'] = struct.unpack('f', data[52:56])[0]
            
            # Wheel slip (4 floats)
            parsed['wheelSlip_FL'] = struct.unpack('f', data[60:64])[0]
            parsed['wheelSlip_FR'] = struct.unpack('f', data[64:68])[0]
            parsed['wheelSlip_RL'] = struct.unpack('f', data[68:72])[0]
            parsed['wheelSlip_RR'] = struct.unpack('f', data[72:76])[0]
            
            # Wheel load (4 floats)
            parsed['wheelLoad_FL'] = struct.unpack('f', data[76:80])[0]
            parsed['wheelLoad_FR'] = struct.unpack('f', data[80:84])[0]
            parsed['wheelLoad_RL'] = struct.unpack('f', data[84:88])[0]
            parsed['wheelLoad_RR'] = struct.unpack('f', data[88:92])[0]
            
            # Wheel pressure (4 floats)
            parsed['wheelPressure_FL'] = struct.unpack('f', data[92:96])[0]
            parsed['wheelPressure_FR'] = struct.unpack('f', data[96:100])[0]
            parsed['wheelPressure_RL'] = struct.unpack('f', data[100:104])[0]
            parsed['wheelPressure_RR'] = struct.unpack('f', data[104:108])[0]
            
            # Wheel angular speed (4 floats)
            parsed['wheelAngularSpeed_FL'] = struct.unpack('f', data[108:112])[0]
            parsed['wheelAngularSpeed_FR'] = struct.unpack('f', data[112:116])[0]
            parsed['wheelAngularSpeed_RL'] = struct.unpack('f', data[116:120])[0]
            parsed['wheelAngularSpeed_RR'] = struct.unpack('f', data[120:124])[0]
            
            # Tyre wear (4 floats)
            parsed['tyreWear_FL'] = struct.unpack('f', data[124:128])[0]
            parsed['tyreWear_FR'] = struct.unpack('f', data[128:132])[0]
            parsed['tyreWear_RL'] = struct.unpack('f', data[132:136])[0]
            parsed['tyreWear_RR'] = struct.unpack('f', data[136:140])[0]
            
            # Tyre dirty level (4 floats)
            parsed['tyreDirty_FL'] = struct.unpack('f', data[140:144])[0]
            parsed['tyreDirty_FR'] = struct.unpack('f', data[144:148])[0]
            parsed['tyreDirty_RL'] = struct.unpack('f', data[148:152])[0]
            parsed['tyreDirty_RR'] = struct.unpack('f', data[152:156])[0]
            
            # Tyre core temperature (4 floats)
            parsed['tyreCoreTemp_FL'] = struct.unpack('f', data[156:160])[0]
            parsed['tyreCoreTemp_FR'] = struct.unpack('f', data[160:164])[0]
            parsed['tyreCoreTemp_RL'] = struct.unpack('f', data[164:168])[0]
            parsed['tyreCoreTemp_RR'] = struct.unpack('f', data[168:172])[0]
            
            # Camber RAD (4 floats)
            parsed['camberRAD_FL'] = struct.unpack('f', data[172:176])[0]
            parsed['camberRAD_FR'] = struct.unpack('f', data[176:180])[0]
            parsed['camberRAD_RL'] = struct.unpack('f', data[180:184])[0]
            parsed['camberRAD_RR'] = struct.unpack('f', data[184:188])[0]
            
            # Suspension travel (4 floats)
            parsed['suspensionTravel_FL'] = struct.unpack('f', data[188:192])[0]
            parsed['suspensionTravel_FR'] = struct.unpack('f', data[192:196])[0]
            parsed['suspensionTravel_RL'] = struct.unpack('f', data[196:200])[0]
            parsed['suspensionTravel_RR'] = struct.unpack('f', data[200:204])[0]
            
            # DRS, TC, Heading, Pitch, Roll
            parsed['drs'] = struct.unpack('f', data[204:208])[0]
            parsed['tc'] = struct.unpack('f', data[208:212])[0]
            parsed['heading'] = struct.unpack('f', data[212:216])[0]
            parsed['pitch'] = struct.unpack('f', data[216:220])[0]
            parsed['roll'] = struct.unpack('f', data[220:224])[0]
            
            # CG Height
            parsed['cgHeight'] = struct.unpack('f', data[224:228])[0]
            
            # Car damage (5 floats)
            parsed['carDamage_front'] = struct.unpack('f', data[228:232])[0]
            parsed['carDamage_rear'] = struct.unpack('f', data[232:236])[0]
            parsed['carDamage_left'] = struct.unpack('f', data[236:240])[0]
            parsed['carDamage_right'] = struct.unpack('f', data[240:244])[0]
            parsed['carDamage_centre'] = struct.unpack('f', data[244:248])[0]
            
            # Número de neumáticos fuera
            parsed['numberOfTyresOut'] = struct.unpack('i', data[248:252])[0]
            
            # Pit limiter
            parsed['pitLimiterOn'] = struct.unpack('i', data[252:256])[0]
            
            # ABS
            parsed['abs'] = struct.unpack('f', data[256:260])[0]
            
            return parsed
            
        except Exception as e:
            return {'error': str(e)}
    
    def read_and_parse_graphics(self) -> Dict[str, Any]:
        """Lee y parsea datos de Graphics"""
        if not self.graphics_handle:
            return {}
        
        try:
            self.graphics_handle.seek(0)
            data = self.graphics_handle.read(2048)
            
            parsed = {}
            
            parsed['packetId'] = struct.unpack('i', data[0:4])[0]
            parsed['status'] = struct.unpack('i', data[4:8])[0]
            parsed['session'] = struct.unpack('i', data[8:12])[0]
            
            # Tiempos
            parsed['currentTime'] = struct.unpack('i', data[12:16])[0]
            parsed['lastTime'] = struct.unpack('i', data[16:20])[0]
            parsed['bestTime'] = struct.unpack('i', data[20:24])[0]
            parsed['split'] = struct.unpack('i', data[24:28])[0]
            parsed['completedLaps'] = struct.unpack('i', data[28:32])[0]
            parsed['position'] = struct.unpack('i', data[32:36])[0]
            parsed['iCurrentTime'] = struct.unpack('i', data[36:40])[0]
            parsed['iLastTime'] = struct.unpack('i', data[40:44])[0]
            parsed['iBestTime'] = struct.unpack('i', data[44:48])[0]
            
            parsed['sessionTimeLeft'] = struct.unpack('f', data[48:52])[0]
            parsed['distanceTraveled'] = struct.unpack('f', data[52:56])[0]
            parsed['isInPit'] = struct.unpack('i', data[56:60])[0]
            parsed['currentSectorIndex'] = struct.unpack('i', data[60:64])[0]
            parsed['lastSectorTime'] = struct.unpack('i', data[64:68])[0]
            parsed['numberOfLaps'] = struct.unpack('i', data[68:72])[0]
            
            # Compound de neumático
            parsed['tyreCompound'] = data[72:105].decode('utf-16-le', errors='ignore').rstrip('\x00')
            
            parsed['replayTimeMultiplier'] = struct.unpack('f', data[108:112])[0]
            parsed['normalizedCarPosition'] = struct.unpack('f', data[112:116])[0]
            
            # Active cars
            parsed['activeCars'] = struct.unpack('i', data[116:120])[0]
            
            # Coordenadas del coche (vec3 de floats)
            parsed['carCoordinates_x'] = struct.unpack('f', data[120:124])[0]
            parsed['carCoordinates_y'] = struct.unpack('f', data[124:128])[0]
            parsed['carCoordinates_z'] = struct.unpack('f', data[128:132])[0]
            
            parsed['carID'] = struct.unpack('i', data[132:136])[0]
            
            return parsed
            
        except Exception as e:
            return {'error': str(e)}
    
    def read_and_parse_static(self) -> Dict[str, Any]:
        """Lee y parsea datos de Static"""
        if not self.static_handle:
            return {}
        
        try:
            self.static_handle.seek(0)
            data = self.static_handle.read(2048)
            
            parsed = {}
            
            parsed['smVersion'] = data[0:15].decode('utf-16-le', errors='ignore').rstrip('\x00')
            parsed['acVersion'] = data[15:30].decode('utf-16-le', errors='ignore').rstrip('\x00')
            
            parsed['numberOfSessions'] = struct.unpack('i', data[30:34])[0]
            parsed['numCars'] = struct.unpack('i', data[34:38])[0]
            
            parsed['carModel'] = data[38:138].decode('utf-16-le', errors='ignore').rstrip('\x00')
            parsed['track'] = data[138:238].decode('utf-16-le', errors='ignore').rstrip('\x00')
            parsed['playerName'] = data[238:338].decode('utf-16-le', errors='ignore').rstrip('\x00')
            parsed['playerSurname'] = data[338:438].decode('utf-16-le', errors='ignore').rstrip('\x00')
            parsed['playerNick'] = data[438:538].decode('utf-16-le', errors='ignore').rstrip('\x00')
            
            parsed['sectorCount'] = struct.unpack('i', data[538:542])[0]
            
            parsed['maxTorque'] = struct.unpack('f', data[546:550])[0]
            parsed['maxPower'] = struct.unpack('f', data[550:554])[0]
            parsed['maxRpm'] = struct.unpack('i', data[554:558])[0]
            parsed['maxFuel'] = struct.unpack('f', data[558:562])[0]
            
            parsed['suspensionMaxTravel_FL'] = struct.unpack('f', data[562:566])[0]
            parsed['suspensionMaxTravel_FR'] = struct.unpack('f', data[566:570])[0]
            parsed['suspensionMaxTravel_RL'] = struct.unpack('f', data[570:574])[0]
            parsed['suspensionMaxTravel_RR'] = struct.unpack('f', data[574:578])[0]
            
            parsed['tyreRadius_FL'] = struct.unpack('f', data[578:582])[0]
            parsed['tyreRadius_FR'] = struct.unpack('f', data[582:586])[0]
            parsed['tyreRadius_RL'] = struct.unpack('f', data[586:590])[0]
            parsed['tyreRadius_RR'] = struct.unpack('f', data[590:594])[0]
            
            parsed['maxTurboBoost'] = struct.unpack('f', data[594:598])[0]
            
            parsed['penaltiesEnabled'] = struct.unpack('i', data[602:606])[0]
            parsed['aidFuelRate'] = struct.unpack('f', data[606:610])[0]
            parsed['aidTireRate'] = struct.unpack('f', data[610:614])[0]
            parsed['aidMechanicalDamage'] = struct.unpack('f', data[614:618])[0]
            parsed['aidAllowTyreBlankets'] = struct.unpack('i', data[618:622])[0]
            parsed['aidStability'] = struct.unpack('f', data[622:626])[0]
            parsed['aidAutoClutch'] = struct.unpack('i', data[626:630])[0]
            parsed['aidAutoBlip'] = struct.unpack('i', data[630:634])[0]
            
            parsed['pitWindowStart'] = struct.unpack('i', data[638:642])[0]
            parsed['pitWindowEnd'] = struct.unpack('i', data[642:646])[0]
            parsed['isOnline'] = struct.unpack('i', data[646:650])[0]
            
            parsed['dryTyresName'] = data[650:750].decode('utf-16-le', errors='ignore').rstrip('\x00')
            parsed['wetTyresName'] = data[750:850].decode('utf-16-le', errors='ignore').rstrip('\x00')
            
            return parsed
            
        except Exception as e:
            return {'error': str(e)}
    
    def update_panel(self, labels_dict: dict, data: Dict[str, Any]):
        """Actualiza un panel con nuevos datos"""
        if 'grid' not in labels_dict:
            return
        
        grid = labels_dict['grid']
        
        # Ordenar las claves para mantener orden consistente
        sorted_keys = sorted(data.keys())
        
        row = 0
        for key in sorted_keys:
            value = data[key]
            
            # Si no existe el label, crearlo
            if key not in labels_dict:
                name_label = QLabel(f"{key}:")
                name_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px; font-family: 'Consolas', 'Monaco', monospace;")
                
                value_label = QLabel()
                value_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 600; font-family: 'Consolas', 'Monaco', monospace;")
                
                grid.addWidget(name_label, row, 0)
                grid.addWidget(value_label, row, 1)
                
                labels_dict[key] = value_label
            
            # Actualizar valor
            if isinstance(value, float):
                labels_dict[key].setText(f"{value:.3f}")
            elif isinstance(value, int):
                labels_dict[key].setText(str(value))
            else:
                labels_dict[key].setText(str(value)[:50])  # Limitar strings largos
            
            row += 1
