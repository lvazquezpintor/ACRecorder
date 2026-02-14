"""
Pestaña de Shared Memory - Visualización en tiempo real de TODOS los datos
Soporta múltiples simuladores de la familia Assetto Corsa
CORREGIDO según estructuras C++ de ACC con #pragma pack(4)
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
            'size': 4096  # Aumentado para seguridad
        },
        'AC': {
            'physics': 'Local\\acpmf_physics',
            'graphics': 'Local\\acpmf_graphics',
            'static': 'Local\\acpmf_static',
            'size': 4096
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
        """Lee y parsea SPageFilePhysics según estructura C++ con pack(4)"""
        if not self.physics_handle:
            return {}
        
        try:
            self.physics_handle.seek(0)
            data = self.physics_handle.read(4096)
            
            parsed = {}
            offset = 0
            
            # Estructura C++ exacta con pack(4)
            parsed['packetId'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['gas'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['brake'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['fuel'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['gear'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['rpms'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['steerAngle'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['speedKmh'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # velocity[3]
            parsed['velocity[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['velocity[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['velocity[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # accG[3]
            parsed['accG[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['accG[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['accG[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelSlip[4]
            parsed['wheelSlip[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelSlip[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelSlip[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelSlip[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelLoad[4]
            parsed['wheelLoad[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelLoad[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelLoad[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelLoad[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelsPressure[4]
            parsed['wheelPress[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelPress[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelPress[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelPress[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelAngularSpeed[4]
            parsed['wheelAngSpeed[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelAngSpeed[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelAngSpeed[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wheelAngSpeed[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreWear[4]
            parsed['tyreWear[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreWear[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreWear[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreWear[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreDirtyLevel[4]
            parsed['tyreDirty[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreDirty[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreDirty[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreDirty[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreCoreTemperature[4]
            parsed['tyreCoreTemp[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreCoreTemp[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreCoreTemp[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreCoreTemp[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # camberRAD[4]
            parsed['camberRAD[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['camberRAD[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['camberRAD[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['camberRAD[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # suspensionTravel[4]
            parsed['suspTravel[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['suspTravel[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['suspTravel[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['suspTravel[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            parsed['drs'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tc'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['heading'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['pitch'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['roll'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['cgHeight'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # carDamage[5]
            parsed['damage[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['damage[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['damage[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['damage[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['damage[4]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            parsed['tyresOut'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['pitLimiter'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['abs'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # kersCharge, kersInput (not used in ACC)
            offset += 8
            
            parsed['autoShifter'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # rideHeight[2]
            parsed['rideHeight[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['rideHeight[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            parsed['turboBoost'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['ballast'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['airDensity'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['airTemp'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['roadTemp'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # localAngularVel[3]
            parsed['localAngVel[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['localAngVel[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['localAngVel[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            parsed['finalFF'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['perfMeter'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # engineBrake, ers fields (not used in ACC) - 6 ints + 1 float = 28 bytes
            offset += 28
            
            # brakeTemp[4]
            parsed['brakeTemp[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['brakeTemp[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['brakeTemp[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['brakeTemp[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            parsed['clutch'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreTempI[4], tyreTempM[4], tyreTempO[4] - 12 floats
            offset += 48
            
            parsed['isAI'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # tyreContactPoint[4][3], tyreContactNormal[4][3], tyreContactHeading[4][3] - 36 floats
            offset += 144
            
            parsed['brakeBias'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # localVelocity[3]
            parsed['localVel[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['localVel[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['localVel[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # P2P - 2 ints
            offset += 8
            
            parsed['currentMaxRpm'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # mz[4], fx[4], fy[4] - 12 floats
            offset += 48
            
            # slipRatio[4]
            parsed['slipRatio[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['slipRatio[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['slipRatio[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['slipRatio[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # slipAngle[4]
            parsed['slipAngle[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['slipAngle[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['slipAngle[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['slipAngle[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            parsed['tcinAction'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['absInAction'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # suspensionDamage[4]
            parsed['suspDamage[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['suspDamage[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['suspDamage[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['suspDamage[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreTemp[4]
            parsed['tyreTemp[0]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreTemp[1]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreTemp[2]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreTemp[3]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            return parsed
            
        except Exception as e:
            return {'error': str(e)}
    
    def read_and_parse_graphics(self) -> Dict[str, Any]:
        """Lee y parsea SPageFileGraphic según estructura C++ con pack(4)"""
        if not self.graphics_handle:
            return {}
        
        try:
            self.graphics_handle.seek(0)
            data = self.graphics_handle.read(4096)
            
            parsed = {}
            offset = 0
            
            parsed['packetId'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['status'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['session'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # wchar_t[15] = 30 bytes
            parsed['currentTime'] = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            parsed['lastTime'] = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            parsed['bestTime'] = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            parsed['split'] = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            
            parsed['completedLaps'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['position'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['iCurrentTime'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['iLastTime'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['iBestTime'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['sessionTimeLeft'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['distanceTraveled'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['isInPit'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['currentSector'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['lastSectorTime'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['numberOfLaps'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # wchar_t[33] = 66 bytes
            parsed['tyreCompound'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            
            parsed['replayMult'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['normalizedPos'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['activeCars'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # carCoordinates[60][3] - 180 floats - solo mostramos primeros
            for i in range(3):
                parsed[f'carCoord[0][{i}]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            offset += 708  # Saltamos el resto (57 * 3 floats)
            
            # carID[60] - 60 ints - solo mostramos primero
            parsed['carID[0]'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            offset += 236  # Saltamos el resto (59 ints)
            
            parsed['playerCarID'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['penaltyTime'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['flag'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['penalty'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['idealLineOn'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['isInPitLane'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['surfaceGrip'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['mandPitDone'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['windSpeed'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['windDirection'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['setupMenuVis'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['mainDisplay'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['secDisplay'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['TC'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['TCCut'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['EngineMap'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['ABS'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['fuelXLap'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['rainLights'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['flashLights'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['lightsStage'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['exhaustTemp'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['wiperLV'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['stintTotal'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['stintTime'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['rainTyres'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            return parsed
            
        except Exception as e:
            return {'error': str(e)}
    
    def read_and_parse_static(self) -> Dict[str, Any]:
        """Lee y parsea SPageFileStatic según estructura C++ con pack(4)"""
        if not self.static_handle:
            return {}
        
        try:
            self.static_handle.seek(0)
            data = self.static_handle.read(4096)
            
            parsed = {}
            offset = 0
            
            # wchar_t[15] = 30 bytes
            parsed['smVersion'] = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            parsed['acVersion'] = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            
            parsed['numSessions'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['numCars'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # wchar_t[33] = 66 bytes
            parsed['carModel'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            parsed['track'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            parsed['playerName'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            parsed['playerSurname'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            parsed['playerNick'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            
            parsed['sectorCount'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['maxTorque'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['maxPower'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['maxRpm'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['maxFuel'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # suspensionMaxTravel[4]
            for i in range(4):
                parsed[f'suspMaxTravel[{i}]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreRadius[4]
            for i in range(4):
                parsed[f'tyreRadius[{i}]'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            parsed['maxTurbo'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # deprecated_1, deprecated_2
            offset += 8
            
            parsed['penaltiesOn'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['aidFuelRate'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['aidTyreRate'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['aidMechDmg'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['tyreBlankets'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['aidStability'] = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            parsed['aidAutoClutch'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['aidAutoBlip'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # DRS/ERS/KERS fields
            offset += 32  # hasDRS, hasERS, hasKERS, kersMaxJ, engineBrakeSettingsCount, ersPowerControllerCount, trackSPlineLength, ersMaxJ
            
            # wchar_t[33] = 66 bytes
            parsed['trackConfig'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            
            offset += 4  # ersMaxJ ya contado arriba, saltar otros campos
            
            parsed['isTimedRace'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['hasExtraLap'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # wchar_t[33] = 66 bytes
            parsed['carSkin'] = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            
            parsed['reversedGrid'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['pitWinStart'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['pitWinEnd'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            parsed['isOnline'] = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
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
