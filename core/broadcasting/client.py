"""
ACC Broadcasting Client - Cliente UDP para Broadcasting SDK
"""

import socket
import struct
import threading
import time
from typing import Dict, List, Optional, Callable
from io import BytesIO

from .protocol import (
    InboundMessageTypes, 
    OutboundMessageTypes,
    BroadcastingCarLocationEnum,
    SessionType,
    CarModelType,
    DriverCategory,
    CupCategory
)


class ACCBroadcastingClient:
    """Cliente para conectar con el Broadcasting SDK de ACC"""
    
    BROADCASTING_PROTOCOL_VERSION = 4
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.running = False
        self.receive_thread = None
        
        # Datos recibidos
        self.entry_list = {}  # {car_index: CarInfo}
        self.realtime_data = {}  # {car_index: RealtimeCarUpdate}
        self.session_info = {}
        self.track_data = {}
        
        # Callbacks opcionales
        self.on_entry_list_update = None
        self.on_realtime_update = None
        self.on_realtime_car_update = None
        
    def connect(self, 
                display_name: str = "ACCRecorder",
                ip: str = "127.0.0.1",
                port: int = 9000,
                password: str = "asd",
                command_password: str = "",
                update_interval_ms: int = 250) -> bool:
        """
        Conecta con el servidor de Broadcasting de ACC
        
        Args:
            display_name: Nombre de la aplicación
            ip: IP del servidor ACC
            port: Puerto (por defecto 9000)
            password: Password configurado en broadcasting.json
            command_password: Password de comandos
            update_interval_ms: Intervalo de actualización en ms (por defecto 250ms = 4Hz)
        """
        try:
            # Crear socket UDP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(1.0)
            self.server_address = (ip, port)
            
            # Enviar registro
            self._send_register_command(display_name, password, update_interval_ms, command_password)
            
            # Esperar confirmación
            time.sleep(0.5)
            
            # Solicitar datos iniciales
            self._request_entry_list()
            self._request_track_data()
            
            # Iniciar thread de recepción
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            self.connected = True
            print(f"Conectado al Broadcasting de ACC en {ip}:{port}")
            return True
            
        except Exception as e:
            print(f"Error conectando al Broadcasting: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta del servidor"""
        if self.socket:
            try:
                self._send_unregister_command()
                self.running = False
                if self.receive_thread:
                    self.receive_thread.join(timeout=2.0)
                self.socket.close()
            except:
                pass
        self.connected = False
        print("Desconectado del Broadcasting de ACC")
    
    def get_standings(self) -> List[Dict]:
        """
        Obtiene la clasificación actual ordenada por posición
        
        Returns:
            Lista de diccionarios con información de cada piloto ordenada por posición
        """
        standings = []
        
        for car_index, realtime in self.realtime_data.items():
            if car_index not in self.entry_list:
                continue
                
            entry = self.entry_list[car_index]
            
            # Obtener piloto actual
            current_driver = None
            if realtime['driver_index'] < len(entry['drivers']):
                current_driver = entry['drivers'][realtime['driver_index']]
            
            driver_name = "Unknown"
            if current_driver:
                driver_name = f"{current_driver['first_name']} {current_driver['last_name']}".strip()
                if not driver_name:
                    driver_name = current_driver.get('short_name', 'Unknown')
            
            standings.append({
                'position': realtime['position'],
                'car_index': car_index,
                'car_number': entry['race_number'],
                'driver_name': driver_name,
                'team_name': entry['team_name'],
                'car_model': entry['car_model_type'],
                'laps': realtime['laps'],
                'delta': realtime['delta'],
                'best_session_lap': realtime['best_session_lap'],
                'last_lap': realtime['last_lap'],
                'current_lap': realtime['current_lap'],
                'location': realtime['car_location']
            })
        
        # Ordenar por posición
        standings.sort(key=lambda x: x['position'])
        
        return standings
    
    def get_session_info(self) -> Dict:
        """Obtiene información de la sesión actual"""
        return self.session_info.copy()
    
    def get_track_data(self) -> Dict:
        """Obtiene información del circuito"""
        return self.track_data.copy()
    
    # ========== MÉTODOS PRIVADOS ==========
    
    def _send_register_command(self, display_name: str, password: str, 
                               update_interval_ms: int, command_password: str):
        """Envía comando de registro"""
        buffer = BytesIO()
        
        # Tipo de mensaje
        buffer.write(struct.pack('B', OutboundMessageTypes.REGISTER_COMMAND_APPLICATION))
        
        # Versión del protocolo
        buffer.write(struct.pack('B', self.BROADCASTING_PROTOCOL_VERSION))
        
        # Display name (string con longitud)
        name_bytes = display_name.encode('utf-8')
        buffer.write(struct.pack('B', len(name_bytes)))
        buffer.write(name_bytes)
        
        # Connection password (string con longitud)
        pwd_bytes = password.encode('utf-8')
        buffer.write(struct.pack('B', len(pwd_bytes)))
        buffer.write(pwd_bytes)
        
        # Update interval
        buffer.write(struct.pack('i', update_interval_ms))
        
        # Command password (string con longitud)
        cmd_pwd_bytes = command_password.encode('utf-8')
        buffer.write(struct.pack('B', len(cmd_pwd_bytes)))
        buffer.write(cmd_pwd_bytes)
        
        self.socket.sendto(buffer.getvalue(), self.server_address)
    
    def _send_unregister_command(self):
        """Envía comando de desregistro"""
        buffer = BytesIO()
        buffer.write(struct.pack('B', OutboundMessageTypes.UNREGISTER_COMMAND_APPLICATION))
        buffer.write(struct.pack('i', 1))  # Connection ID
        self.socket.sendto(buffer.getvalue(), self.server_address)
    
    def _request_entry_list(self):
        """Solicita la lista de participantes"""
        buffer = BytesIO()
        buffer.write(struct.pack('B', OutboundMessageTypes.REQUEST_ENTRY_LIST))
        buffer.write(struct.pack('i', 1))  # Connection ID
        self.socket.sendto(buffer.getvalue(), self.server_address)
    
    def _request_track_data(self):
        """Solicita información del circuito"""
        buffer = BytesIO()
        buffer.write(struct.pack('B', OutboundMessageTypes.REQUEST_TRACK_DATA))
        buffer.write(struct.pack('i', 1))  # Connection ID
        self.socket.sendto(buffer.getvalue(), self.server_address)
    
    def _receive_loop(self):
        """Loop de recepción de datos"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(2048)
                self._process_message(data)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error en receive_loop: {e}")
    
    def _process_message(self, data: bytes):
        """Procesa un mensaje recibido"""
        if len(data) < 1:
            return
        
        message_type = data[0]
        
        if message_type == InboundMessageTypes.REGISTRATION_RESULT:
            self._process_registration_result(data)
        elif message_type == InboundMessageTypes.REALTIME_UPDATE:
            self._process_realtime_update(data)
        elif message_type == InboundMessageTypes.REALTIME_CAR_UPDATE:
            self._process_realtime_car_update(data)
        elif message_type == InboundMessageTypes.ENTRY_LIST:
            self._process_entry_list(data)
        elif message_type == InboundMessageTypes.ENTRY_LIST_CAR:
            self._process_entry_list_car(data)
        elif message_type == InboundMessageTypes.TRACK_DATA:
            self._process_track_data(data)
        elif message_type == InboundMessageTypes.BROADCASTING_EVENT:
            self._process_broadcasting_event(data)
    
    def _process_registration_result(self, data: bytes):
        """Procesa resultado de registro"""
        reader = BytesIO(data[1:])
        connection_id = struct.unpack('i', reader.read(4))[0]
        success = struct.unpack('B', reader.read(1))[0]
        is_readonly = struct.unpack('B', reader.read(1))[0]
        
        err_msg_len = struct.unpack('B', reader.read(1))[0]
        error_msg = ""
        if err_msg_len > 0:
            error_msg = reader.read(err_msg_len).decode('utf-8')
        
        if success:
            print(f"Registro exitoso! Connection ID: {connection_id}")
        else:
            print(f"Error en registro: {error_msg}")
    
    def _process_realtime_update(self, data: bytes):
        """Procesa actualización de sesión en tiempo real"""
        reader = BytesIO(data[1:])
        
        event_index = struct.unpack('H', reader.read(2))[0]
        session_index = struct.unpack('H', reader.read(2))[0]
        session_type = struct.unpack('B', reader.read(1))[0]
        phase = struct.unpack('B', reader.read(1))[0]
        
        session_time = struct.unpack('f', reader.read(4))[0]
        session_end_time = struct.unpack('f', reader.read(4))[0]
        focused_car_index = struct.unpack('i', reader.read(4))[0]
        
        # Camera set (string)
        cam_set_len = struct.unpack('B', reader.read(1))[0]
        active_camera_set = reader.read(cam_set_len).decode('utf-8') if cam_set_len > 0 else ""
        
        # Camera (string)
        cam_len = struct.unpack('B', reader.read(1))[0]
        active_camera = reader.read(cam_len).decode('utf-8') if cam_len > 0 else ""
        
        # HUD page (string)
        hud_len = struct.unpack('B', reader.read(1))[0]
        current_hud_page = reader.read(hud_len).decode('utf-8') if hud_len > 0 else ""
        
        # Replay
        is_replay_playing = struct.unpack('B', reader.read(1))[0]
        
        if is_replay_playing:
            replay_session_time = struct.unpack('f', reader.read(4))[0]
            replay_remaining_time = struct.unpack('f', reader.read(4))[0]
        
        time_of_day = struct.unpack('f', reader.read(4))[0]
        ambient_temp = struct.unpack('B', reader.read(1))[0]
        track_temp = struct.unpack('B', reader.read(1))[0]
        clouds = struct.unpack('B', reader.read(1))[0] / 10.0
        rain_level = struct.unpack('B', reader.read(1))[0] / 10.0
        wetness = struct.unpack('B', reader.read(1))[0] / 10.0
        
        # Best session lap
        best_session_lap = self._read_lap_info(reader)
        
        self.session_info = {
            'event_index': event_index,
            'session_index': session_index,
            'session_type': session_type,
            'phase': phase,
            'session_time': session_time,
            'session_end_time': session_end_time,
            'focused_car_index': focused_car_index,
            'time_of_day': time_of_day,
            'ambient_temp': ambient_temp,
            'track_temp': track_temp,
            'clouds': clouds,
            'rain_level': rain_level,
            'wetness': wetness,
            'best_session_lap': best_session_lap
        }
        
        if self.on_realtime_update:
            self.on_realtime_update(self.session_info)
    
    def _process_realtime_car_update(self, data: bytes):
        """Procesa actualización de coches en tiempo real"""
        reader = BytesIO(data[1:])
        
        car_index = struct.unpack('H', reader.read(2))[0]
        driver_index = struct.unpack('H', reader.read(2))[0]
        driver_count = struct.unpack('B', reader.read(1))[0]
        gear = struct.unpack('b', reader.read(1))[0]  # signed
        world_pos_x = struct.unpack('f', reader.read(4))[0]
        world_pos_y = struct.unpack('f', reader.read(4))[0]
        yaw = struct.unpack('f', reader.read(4))[0]
        car_location = struct.unpack('B', reader.read(1))[0]
        kmh = struct.unpack('H', reader.read(2))[0]
        position = struct.unpack('H', reader.read(2))[0]
        cup_position = struct.unpack('H', reader.read(2))[0]
        track_position = struct.unpack('H', reader.read(2))[0]
        spline_position = struct.unpack('f', reader.read(4))[0]
        laps = struct.unpack('H', reader.read(2))[0]
        delta = struct.unpack('i', reader.read(4))[0]
        
        best_session_lap = self._read_lap_info(reader)
        last_lap = self._read_lap_info(reader)
        current_lap = self._read_lap_info(reader)
        
        self.realtime_data[car_index] = {
            'driver_index': driver_index,
            'driver_count': driver_count,
            'gear': gear,
            'world_pos_x': world_pos_x,
            'world_pos_y': world_pos_y,
            'yaw': yaw,
            'car_location': car_location,
            'kmh': kmh,
            'position': position,
            'cup_position': cup_position,
            'track_position': track_position,
            'spline_position': spline_position,
            'laps': laps,
            'delta': delta,
            'best_session_lap': best_session_lap,
            'last_lap': last_lap,
            'current_lap': current_lap
        }
        
        if self.on_realtime_car_update:
            self.on_realtime_car_update(car_index, self.realtime_data[car_index])
    
    def _process_entry_list(self, data: bytes):
        """Procesa lista de participantes"""
        reader = BytesIO(data[1:])
        
        connection_id = struct.unpack('i', reader.read(4))[0]
        car_entry_count = struct.unpack('H', reader.read(2))[0]
        
        # Leer índices de coches
        for _ in range(car_entry_count):
            car_index = struct.unpack('H', reader.read(2))[0]
            # Aquí solo recibimos los índices, los detalles vienen en ENTRY_LIST_CAR
    
    def _process_entry_list_car(self, data: bytes):
        """Procesa entrada de un coche específico"""
        reader = BytesIO(data[1:])
        
        car_index = struct.unpack('H', reader.read(2))[0]
        car_model_type = struct.unpack('B', reader.read(1))[0]
        
        # Team name
        team_name_len = struct.unpack('B', reader.read(1))[0]
        team_name = reader.read(team_name_len).decode('utf-8') if team_name_len > 0 else ""
        
        race_number = struct.unpack('i', reader.read(4))[0]
        cup_category = struct.unpack('B', reader.read(1))[0]
        current_driver_index = struct.unpack('B', reader.read(1))[0]
        nationality = struct.unpack('H', reader.read(2))[0]
        
        # Drivers
        driver_count = struct.unpack('B', reader.read(1))[0]
        drivers = []
        
        for _ in range(driver_count):
            # First name
            fname_len = struct.unpack('B', reader.read(1))[0]
            first_name = reader.read(fname_len).decode('utf-8') if fname_len > 0 else ""
            
            # Last name
            lname_len = struct.unpack('B', reader.read(1))[0]
            last_name = reader.read(lname_len).decode('utf-8') if lname_len > 0 else ""
            
            # Short name
            sname_len = struct.unpack('B', reader.read(1))[0]
            short_name = reader.read(sname_len).decode('utf-8') if sname_len > 0 else ""
            
            category = struct.unpack('B', reader.read(1))[0]
            driver_nationality = struct.unpack('H', reader.read(2))[0]
            
            drivers.append({
                'first_name': first_name,
                'last_name': last_name,
                'short_name': short_name,
                'category': category,
                'nationality': driver_nationality
            })
        
        self.entry_list[car_index] = {
            'car_model_type': car_model_type,
            'team_name': team_name,
            'race_number': race_number,
            'cup_category': cup_category,
            'current_driver_index': current_driver_index,
            'nationality': nationality,
            'drivers': drivers
        }
        
        if self.on_entry_list_update:
            self.on_entry_list_update(car_index, self.entry_list[car_index])
    
    def _process_track_data(self, data: bytes):
        """Procesa información del circuito"""
        reader = BytesIO(data[1:])
        
        connection_id = struct.unpack('i', reader.read(4))[0]
        
        # Track name
        name_len = struct.unpack('B', reader.read(1))[0]
        track_name = reader.read(name_len).decode('utf-8') if name_len > 0 else ""
        
        track_id = struct.unpack('i', reader.read(4))[0]
        track_meters = struct.unpack('i', reader.read(4))[0]
        
        # Camera sets
        camera_set_count = struct.unpack('B', reader.read(1))[0]
        camera_sets = []
        for _ in range(camera_set_count):
            set_len = struct.unpack('B', reader.read(1))[0]
            camera_set = reader.read(set_len).decode('utf-8') if set_len > 0 else ""
            camera_sets.append(camera_set)
        
        # HUD pages
        hud_page_count = struct.unpack('B', reader.read(1))[0]
        hud_pages = []
        for _ in range(hud_page_count):
            page_len = struct.unpack('B', reader.read(1))[0]
            hud_page = reader.read(page_len).decode('utf-8') if page_len > 0 else ""
            hud_pages.append(hud_page)
        
        self.track_data = {
            'track_name': track_name,
            'track_id': track_id,
            'track_meters': track_meters,
            'camera_sets': camera_sets,
            'hud_pages': hud_pages
        }
    
    def _process_broadcasting_event(self, data: bytes):
        """Procesa eventos de broadcasting"""
        # Implementación simplificada
        pass
    
    def _read_lap_info(self, reader: BytesIO) -> Dict:
        """Lee información de una vuelta"""
        lap_time_ms = struct.unpack('i', reader.read(4))[0]
        
        # Splits (3 sectores)
        splits = []
        for _ in range(3):
            split_ms = struct.unpack('i', reader.read(4))[0]
            splits.append(split_ms)
        
        is_invalid = struct.unpack('B', reader.read(1))[0]
        is_valid_for_best = struct.unpack('B', reader.read(1))[0]
        
        # Flags
        is_out_lap = (is_invalid >> 0) & 1
        is_in_lap = (is_invalid >> 1) & 1
        
        return {
            'lap_time_ms': lap_time_ms,
            'splits': splits,
            'is_invalid': bool(is_invalid),
            'is_valid_for_best': bool(is_valid_for_best),
            'is_out_lap': bool(is_out_lap),
            'is_in_lap': bool(is_in_lap)
        }
