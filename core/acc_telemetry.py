"""
ACC Telemetry Module - Interfaz para leer datos de Assetto Corsa Competizione
Utiliza memoria compartida (Shared Memory) para acceder a los datos del juego
CORREGIDO según estructuras C++ de ACC con #pragma pack(4)
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
                # Aumentar tamaño del buffer para seguridad
                self.physics_handle = mmap.mmap(-1, 4096, self.PHYSICS_MAP)
                self.graphics_handle = mmap.mmap(-1, 4096, self.GRAPHICS_MAP)
                self.static_handle = mmap.mmap(-1, 4096, self.STATIC_MAP)
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
            data = self.graphics_handle.read(4096)
            
            offset = 0
            
            packet_id = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            status = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            session = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # wchar_t[15] = 30 bytes
            current_time = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            last_time = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            best_time = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            split = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            
            completed_laps = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            position = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            i_current_time = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            i_last_time = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            i_best_time = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            session_time_left = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            distance_traveled = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            is_in_pit = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            current_sector = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            last_sector_time = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            number_of_laps = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # wchar_t[33] = 66 bytes
            tyre_compound = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            
            offset += 4  # replayMult
            normalized_pos = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
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
            
            return {
                'packet_id': packet_id,
                'status': statuses.get(status, 'Unknown'),
                'session_type': session_types.get(session, 'Unknown'),
                'current_time': current_time,
                'last_time': last_time,
                'best_time': best_time,
                'current_time_ms': i_current_time,
                'last_lap_time_ms': i_last_time,
                'best_lap_time_ms': i_best_time,
                'completed_laps': completed_laps,
                'position': position,
                'normalized_position': round(normalized_pos, 4),
                'session_time_left': round(session_time_left, 1),
                'distance_traveled': round(distance_traveled, 1),
                'is_in_pit': bool(is_in_pit),
                'current_sector': current_sector,
                'tyre_compound': tyre_compound,
                'number_of_laps': number_of_laps
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
        """Obtiene telemetría del coche del jugador según estructura C++ con pack(4)"""
        if not self.connected:
            return None
        
        try:
            self.physics_handle.seek(0)
            data = self.physics_handle.read(4096)
            
            offset = 0
            
            # Estructura C++ exacta con pack(4)
            packet_id = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            gas = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            brake = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            fuel = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            gear = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            rpms = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            steer_angle = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            speed_kmh = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # velocity[3]
            velocity_x = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            velocity_y = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            velocity_z = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # accG[3]
            accg_x = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            accg_y = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            accg_z = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelSlip[4]
            wheel_slip_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_slip_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_slip_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_slip_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelLoad[4]
            wheel_load_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_load_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_load_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_load_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelsPressure[4]
            tyre_pressure_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_pressure_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_pressure_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_pressure_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # wheelAngularSpeed[4]
            wheel_angular_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_angular_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_angular_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            wheel_angular_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreWear[4]
            tyre_wear_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_wear_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_wear_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_wear_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # tyreDirtyLevel[4]
            offset += 16  # Saltar dirty level
            
            # tyreCoreTemperature[4]
            tyre_temp_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_temp_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_temp_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            tyre_temp_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # camberRAD[4]
            offset += 16
            
            # suspensionTravel[4]
            susp_travel_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            susp_travel_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            susp_travel_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            susp_travel_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            offset += 4  # drs
            tc = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            heading = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            pitch = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            roll = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            offset += 4  # cgHeight
            
            # carDamage[5]
            offset += 20
            
            offset += 4  # tyresOut
            offset += 4  # pitLimiter
            abs_level = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # kersCharge, kersInput (not used in ACC)
            offset += 8
            
            offset += 4  # autoShifter
            
            # rideHeight[2]
            offset += 8
            
            turbo_boost = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            offset += 4  # ballast
            air_density = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            air_temp = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            road_temp = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # localAngularVel[3]
            offset += 12
            
            offset += 4  # finalFF
            offset += 4  # perfMeter
            
            # engineBrake, ers fields (not used in ACC) - 6 ints + 1 float = 28 bytes
            offset += 28
            
            # brakeTemp[4]
            brake_temp_fl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            brake_temp_fr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            brake_temp_rl = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            brake_temp_rr = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            clutch = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # Detectar bloqueos de rueda
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
                'rpm': rpms,
                'steer_angle': round(steer_angle, 2),
                'speed_kmh': round(speed_kmh, 1),
                'velocity': {
                    'x': round(velocity_x, 2),
                    'y': round(velocity_y, 2),
                    'z': round(velocity_z, 2)
                },
                'g_force': {
                    'lateral': round(accg_x, 2),
                    'longitudinal': round(accg_z, 2),
                    'vertical': round(accg_y, 2)
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
                    'wear': {
                        'front_left': round(tyre_wear_fl, 3),
                        'front_right': round(tyre_wear_fr, 3),
                        'rear_left': round(tyre_wear_rl, 3),
                        'rear_right': round(tyre_wear_rr, 3)
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
                },
                'suspension': {
                    'travel': {
                        'front_left': round(susp_travel_fl, 3),
                        'front_right': round(susp_travel_fr, 3),
                        'rear_left': round(susp_travel_rl, 3),
                        'rear_right': round(susp_travel_rr, 3)
                    }
                },
                'electronics': {
                    'tc': round(tc, 2),
                    'abs': round(abs_level, 2),
                    'clutch': round(clutch, 2)
                },
                'orientation': {
                    'heading': round(heading, 2),
                    'pitch': round(pitch, 2),
                    'roll': round(roll, 2)
                },
                'environment': {
                    'air_temp': round(air_temp, 1),
                    'road_temp': round(road_temp, 1),
                    'air_density': round(air_density, 3)
                },
                'turbo_boost': round(turbo_boost, 2)
            }
            
        except Exception as e:
            print(f"Error leyendo telemetría: {e}")
            return None
    
    def get_car_info(self) -> Optional[Dict]:
        """Obtiene información estática del coche según estructura C++ con pack(4)"""
        if not self.connected:
            return None
        
        try:
            self.static_handle.seek(0)
            data = self.static_handle.read(4096)
            
            offset = 0
            
            # wchar_t[15] = 30 bytes
            sm_version = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            ac_version = data[offset:offset+30].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 30
            
            num_sessions = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            num_cars = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            
            # wchar_t[33] = 66 bytes
            car_model = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            track = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            player_name = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            player_surname = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            player_nick = data[offset:offset+66].decode('utf-16-le', errors='ignore').rstrip('\x00'); offset += 66
            
            sector_count = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            offset += 4  # maxTorque
            offset += 4  # maxPower
            max_rpm = struct.unpack('i', data[offset:offset+4])[0]; offset += 4
            max_fuel = struct.unpack('f', data[offset:offset+4])[0]; offset += 4
            
            # suspensionMaxTravel[4]
            offset += 16
            
            # tyreRadius[4]
            offset += 16
            
            return {
                'sm_version': sm_version,
                'ac_version': ac_version,
                'car_model': car_model,
                'track_name': track,
                'player_name': f"{player_name} {player_surname}".strip(),
                'player_nick': player_nick,
                'max_rpm': max_rpm,
                'max_fuel': round(max_fuel, 1),
                'num_sessions': num_sessions,
                'num_cars': num_cars,
                'sector_count': sector_count
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
