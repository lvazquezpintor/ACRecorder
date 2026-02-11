"""
ACC Telemetry Module - Interfaz para leer datos de Assetto Corsa Competizione
Utiliza memoria compartida (Shared Memory) para acceder a los datos del juego
"""

import mmap
import struct
from ctypes import *
from typing import Dict, List, Optional

class ACCTelemetry:
    """Clase para leer telemetría de ACC mediante Shared Memory"""
    
    # Nombres de memoria compartida de ACC
    PHYSICS_MAP = "Local\\acpmf_physics"
    GRAPHICS_MAP = "Local\\acpmf_graphics"
    STATIC_MAP = "Local\\acpmf_static"
    
    def __init__(self):
        self.physics_handle = None
        self.graphics_handle = None
        self.static_handle = None
        self.connected = False
        
    def connect(self) -> bool:
        """Conecta con la memoria compartida de ACC"""
        try:
            if not self.connected:
                # Intentar abrir las memorias compartidas
                self.physics_handle = mmap.mmap(-1, 1024, self.PHYSICS_MAP)
                self.graphics_handle = mmap.mmap(-1, 1024, self.GRAPHICS_MAP)
                self.static_handle = mmap.mmap(-1, 1024, self.STATIC_MAP)
                self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect(self):
        """Cierra las conexiones de memoria compartida"""
        if self.physics_handle:
            self.physics_handle.close()
        if self.graphics_handle:
            self.graphics_handle.close()
        if self.static_handle:
            self.static_handle.close()
        self.connected = False
    
    def get_session_info(self) -> Optional[Dict]:
        """Obtiene información de la sesión actual"""
        if not self.connected:
            return None
            
        try:
            self.graphics_handle.seek(0)
            data = self.graphics_handle.read(1024)
            
            # Parsear datos básicos de Graphics (estructura simplificada)
            # Offset 0: PacketId (int)
            # Offset 4: AC_STATUS (int)
            # Offset 8: AC_SESSION_TYPE (int)
            
            packet_id = struct.unpack('i', data[0:4])[0]
            status = struct.unpack('i', data[4:8])[0]
            session_type = struct.unpack('i', data[8:12])[0]
            
            session_types = {
                0: 'Unknown',
                1: 'Practice',
                2: 'Qualifying',
                3: 'Race',
                4: 'Hotlap',
                5: 'Time Attack',
                6: 'Drift',
                7: 'Drag'
            }
            
            statuses = {
                0: 'Off',
                1: 'Replay',
                2: 'Live',
                3: 'Pause'
            }
            
            # Más datos de Graphics
            # Offset 12: currentTime (int) - milisegundos
            # Offset 16: lastTime (int)
            # Offset 20: bestTime (int)
            
            current_time = struct.unpack('i', data[12:16])[0]
            last_time = struct.unpack('i', data[16:20])[0]
            best_time = struct.unpack('i', data[20:24])[0]
            
            # Offset 24: completedLaps (int) - Vueltas completadas
            completed_laps = struct.unpack('i', data[24:28])[0]
            
            # Offset 28: position (int) - Posición en carrera
            position = struct.unpack('i', data[28:32])[0]
            
            # Offset 48: normalizedCarPosition (float) - Posición en el circuito (0.0 - 1.0)
            # 0.0 = línea de meta, 0.5 = mitad del circuito, 1.0 = vuelta completa
            normalized_position = struct.unpack('f', data[48:52])[0]
            
            return {
                'packet_id': packet_id,
                'status': statuses.get(status, 'Unknown'),
                'session_type': session_types.get(session_type, 'Unknown'),
                'current_time_ms': current_time,
                'last_lap_time_ms': last_time,
                'best_lap_time_ms': best_time,
                'completed_laps': completed_laps,
                'position': position,
                'normalized_position': round(normalized_position, 4),  # Posición 0.0-1.0 en el circuito
                'is_valid_lap': data[52] == 1,  # Offset 52: isValidLap (byte)
            }
            
        except Exception as e:
            print(f"Error leyendo session info: {e}")
            return None
    
    def get_standings(self) -> List[Dict]:
        """Obtiene las posiciones de los pilotos (simplificado)"""
        if not self.connected:
            return []
        
        try:
            # ACC no expone standings completos en Shared Memory básica
            # Esto requeriría la API de Broadcasting
            # Por ahora retornamos datos simulados o parciales
            
            # En una implementación real, necesitarías:
            # 1. Implementar ACC Broadcasting SDK
            # 2. O usar archivos de resultados de ACC
            
            return [
                {
                    'position': 1,
                    'car_number': 0,
                    'driver_name': 'Player',
                    'gap': '0.000',
                    'laps': 0
                }
            ]
            
        except Exception as e:
            print(f"Error leyendo standings: {e}")
            return []
    
    def get_player_telemetry(self) -> Optional[Dict]:
        """Obtiene telemetría del coche del jugador"""
        if not self.connected:
            return None
        
        try:
            self.physics_handle.seek(0)
            physics_data = self.physics_handle.read(1024)
            
            # Estructura simplificada de Physics
            # Todos los floats son de 4 bytes
            
            # Offset 0: PacketId (int)
            packet_id = struct.unpack('i', physics_data[0:4])[0]
            
            # Offset 4: Gas (float)
            gas = struct.unpack('f', physics_data[4:8])[0]
            
            # Offset 8: Brake (float)
            brake = struct.unpack('f', physics_data[8:12])[0]
            
            # Offset 12: Fuel (float)
            fuel = struct.unpack('f', physics_data[12:16])[0]
            
            # Offset 16-28: Gear (int), RPM (int), SteerAngle (float)
            gear = struct.unpack('i', physics_data[16:20])[0]
            rpm = struct.unpack('i', physics_data[20:24])[0]
            steer_angle = struct.unpack('f', physics_data[24:28])[0]
            
            # Offset 28: SpeedKmh (float)
            speed_kmh = struct.unpack('f', physics_data[28:32])[0]
            
            # Offset 32-44: Velocity (vec3 floats: x, y, z)
            velocity_x = struct.unpack('f', physics_data[32:36])[0]
            velocity_y = struct.unpack('f', physics_data[36:40])[0]
            velocity_z = struct.unpack('f', physics_data[40:44])[0]
            
            # Offset 44-60: AccG (vec3 floats: x, y, z) - Aceleración en G
            accg_x = struct.unpack('f', physics_data[44:48])[0]
            accg_y = struct.unpack('f', physics_data[48:52])[0]
            accg_z = struct.unpack('f', physics_data[52:56])[0]
            
            # Offset 60-76: wheelSlip (4 floats: FL, FR, RL, RR) - Deslizamiento de ruedas
            # Valores > 1.0 indican bloqueo/deslizamiento
            wheel_slip_fl = struct.unpack('f', physics_data[60:64])[0]
            wheel_slip_fr = struct.unpack('f', physics_data[64:68])[0]
            wheel_slip_rl = struct.unpack('f', physics_data[68:72])[0]
            wheel_slip_rr = struct.unpack('f', physics_data[72:76])[0]
            
            # Offset 76-92: wheelLoad (4 floats) - Carga de ruedas en kg
            wheel_load_fl = struct.unpack('f', physics_data[76:80])[0]
            wheel_load_fr = struct.unpack('f', physics_data[80:84])[0]
            wheel_load_rl = struct.unpack('f', physics_data[84:88])[0]
            wheel_load_rr = struct.unpack('f', physics_data[88:92])[0]
            
            # Offset 92-108: wheelsPressure (4 floats) - Presiones de ruedas
            tyre_pressure_fl = struct.unpack('f', physics_data[92:96])[0]
            tyre_pressure_fr = struct.unpack('f', physics_data[96:100])[0]
            tyre_pressure_rl = struct.unpack('f', physics_data[100:104])[0]
            tyre_pressure_rr = struct.unpack('f', physics_data[104:108])[0]
            
            # Offset 108-124: wheelAngularSpeed (4 floats) - Velocidad angular de ruedas
            wheel_angular_fl = struct.unpack('f', physics_data[108:112])[0]
            wheel_angular_fr = struct.unpack('f', physics_data[112:116])[0]
            wheel_angular_rl = struct.unpack('f', physics_data[116:120])[0]
            wheel_angular_rr = struct.unpack('f', physics_data[120:124])[0]
            
            # Offset 124-140: tyreContactPoint (4 vec3, solo leemos primeros 2)
            # Offset 140-156: tyreContactNormal (4 vec3, omitido por brevedad)
            # Offset 156-172: tyreContactHeading (4 vec3, omitido por brevedad)
            
            # Offset 172-188: brakeTempCore (4 floats) - Temperatura núcleo de frenos
            brake_temp_fl = struct.unpack('f', physics_data[172:176])[0]
            brake_temp_fr = struct.unpack('f', physics_data[176:180])[0]
            brake_temp_rl = struct.unpack('f', physics_data[180:184])[0]
            brake_temp_rr = struct.unpack('f', physics_data[184:188])[0]
            
            # Offset 188-204: tyreCoreTemperature (4 floats) - Temperatura núcleo de neumáticos
            tyre_temp_fl = struct.unpack('f', physics_data[188:192])[0]
            tyre_temp_fr = struct.unpack('f', physics_data[192:196])[0]
            tyre_temp_rl = struct.unpack('f', physics_data[196:200])[0]
            tyre_temp_rr = struct.unpack('f', physics_data[200:204])[0]
            
            # Detectar bloqueos de rueda (cuando slip > umbral)
            # Valores típicos: < 1.0 = normal, > 1.2 = deslizamiento, > 2.0 = bloqueo severo
            wheel_lock_fl = wheel_slip_fl > 1.2
            wheel_lock_fr = wheel_slip_fr > 1.2
            wheel_lock_rl = wheel_slip_rl > 1.2
            wheel_lock_rr = wheel_slip_rr > 1.2
            
            return {
                'packet_id': packet_id,
                'gas': round(gas, 3),
                'brake': round(brake, 3),
                'fuel': round(fuel, 2),
                'gear': gear,
                'rpm': rpm,
                'steer_angle': round(steer_angle, 2),
                'speed_kmh': round(speed_kmh, 1),
                'velocity': {
                    'x': round(velocity_x, 2),
                    'y': round(velocity_y, 2),
                    'z': round(velocity_z, 2)
                },
                'g_force': {
                    'lateral': round(accg_x, 2),  # Gs laterales
                    'longitudinal': round(accg_z, 2),  # Gs de frenada/aceleración
                    'vertical': round(accg_y, 2)  # Gs verticales
                },
                'tyres': {
                    'slip': {
                        'front_left': round(wheel_slip_fl, 3),
                        'front_right': round(wheel_slip_fr, 3),
                        'rear_left': round(wheel_slip_rl, 3),
                        'rear_right': round(wheel_slip_rr, 3)
                    },
                    'locked': {
                        'front_left': wheel_lock_fl,
                        'front_right': wheel_lock_fr,
                        'rear_left': wheel_lock_rl,
                        'rear_right': wheel_lock_rr
                    },
                    'temperature': {
                        'front_left': round(tyre_temp_fl, 1),
                        'front_right': round(tyre_temp_fr, 1),
                        'rear_left': round(tyre_temp_rl, 1),
                        'rear_right': round(tyre_temp_rr, 1)
                    },
                    'pressure': {
                        'front_left': round(tyre_pressure_fl, 2),
                        'front_right': round(tyre_pressure_fr, 2),
                        'rear_left': round(tyre_pressure_rl, 2),
                        'rear_right': round(tyre_pressure_rr, 2)
                    },
                    'angular_speed': {
                        'front_left': round(wheel_angular_fl, 1),
                        'front_right': round(wheel_angular_fr, 1),
                        'rear_left': round(wheel_angular_rl, 1),
                        'rear_right': round(wheel_angular_rr, 1)
                    },
                    'load': {
                        'front_left': round(wheel_load_fl, 1),
                        'front_right': round(wheel_load_fr, 1),
                        'rear_left': round(wheel_load_rl, 1),
                        'rear_right': round(wheel_load_rr, 1)
                    }
                },
                'brakes': {
                    'temperature': {
                        'front_left': round(brake_temp_fl, 1),
                        'front_right': round(brake_temp_fr, 1),
                        'rear_left': round(brake_temp_rl, 1),
                        'rear_right': round(brake_temp_rr, 1)
                    }
                }
            }
            
        except Exception as e:
            print(f"Error leyendo telemetría: {e}")
            return None
    
    def get_car_info(self) -> Optional[Dict]:
        """Obtiene información estática del coche"""
        if not self.connected:
            return None
        
        try:
            self.static_handle.seek(0)
            static_data = self.static_handle.read(1024)
            
            # Información estática básica
            max_rpm = struct.unpack('i', static_data[4:8])[0]
            max_fuel = struct.unpack('f', static_data[8:12])[0]
            
            # Nombre del coche (string en offset 12, 50 chars)
            car_model = static_data[12:62].decode('utf-8', errors='ignore').rstrip('\x00')
            
            # Nombre de la pista (string en offset 62, 50 chars)
            track_name = static_data[62:112].decode('utf-8', errors='ignore').rstrip('\x00')
            
            # Offset aproximado 116: trackSPlineLength (float) - Longitud del circuito en metros
            # Este offset puede variar según la versión de ACC
            try:
                track_length = struct.unpack('f', static_data[116:120])[0]
            except:
                track_length = 0.0  # Si no se puede leer, usar 0
            
            return {
                'car_model': car_model,
                'track_name': track_name,
                'track_length_m': round(track_length, 1),  # Longitud del circuito en metros
                'max_rpm': max_rpm,
                'max_fuel': round(max_fuel, 1)
            }
            
        except Exception as e:
            print(f"Error leyendo info del coche: {e}")
            return None


# Implementación alternativa usando Broadcasting SDK para standings completos
class ACCBroadcasting:
    """
    Clase para conectar con ACC Broadcasting SDK (requiere instalación adicional)
    Proporciona acceso a standings y datos de todos los coches
    """
    
    def __init__(self):
        self.connected = False
        # Aquí iría la implementación del Broadcasting SDK
        # Requiere: pip install accbroadcasting
        pass
    
    def connect(self, ip: str = "127.0.0.1", port: int = 9000, 
                display_name: str = "ACC Recorder", password: str = "", 
                update_ms: int = 250):
        """Conecta con el servidor de Broadcasting de ACC"""
        # Implementación del Broadcasting SDK
        pass
    
    def get_session_info(self):
        """Obtiene información completa de la sesión"""
        pass
    
    def get_entry_list(self):
        """Obtiene lista de todos los coches en la sesión"""
        pass
    
    def get_realtime_update(self):
        """Obtiene actualización en tiempo real de posiciones y telemetría"""
        pass
