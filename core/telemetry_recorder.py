"""
Módulo para la grabación de telemetría de ACC con Broadcasting SDK integrado
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional

from .acc_telemetry import ACCTelemetry
from .broadcasting import ACCBroadcastingClient


class TelemetryRecorder:
    """Gestiona la grabación de datos de telemetría de ACC"""
    
    def __init__(self, output_dir: Path, enable_broadcasting: bool = True):
        """
        Inicializa el grabador de telemetría
        
        Args:
            output_dir: Directorio base donde se guardarán las sesiones
            enable_broadcasting: Si True, habilita Broadcasting para obtener posiciones de pilotos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.telemetry_data: List[Dict[str, Any]] = []
        self.current_session_dir: Optional[Path] = None
        self.recording_start_time: Optional[datetime] = None
        
        # Clientes de ACC
        self.acc_telemetry = ACCTelemetry()
        self.broadcasting_client: Optional[ACCBroadcastingClient] = None
        self.enable_broadcasting = enable_broadcasting
        
        # Configuración de Broadcasting
        self.broadcasting_config = {
            'ip': '127.0.0.1',
            'port': 9000,
            'password': 'asd',
            'command_password': '',
            'update_interval_ms': 250
        }
        
        # Frecuencia de muestreo (Hz)
        self.sample_rate = 10  # 10 samples por segundo
        
        # Callbacks
        self.on_telemetry_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[int, float], None]] = None
        self.on_connection_status: Optional[Callable[[bool, bool], None]] = None
        
    def set_broadcasting_config(self, ip: str = '127.0.0.1', port: int = 9000, 
                               password: str = 'asd', update_interval_ms: int = 250):
        """
        Configura los parámetros de Broadcasting
        
        Args:
            ip: IP del servidor ACC
            port: Puerto del Broadcasting (por defecto 9000)
            password: Password configurado en broadcasting.json
            update_interval_ms: Intervalo de actualización en ms
        """
        self.broadcasting_config = {
            'ip': ip,
            'port': port,
            'password': password,
            'command_password': '',
            'update_interval_ms': update_interval_ms
        }
    
    def connect_to_acc(self) -> tuple[bool, bool]:
        """
        Conecta a Shared Memory y Broadcasting de ACC
        
        Returns:
            Tupla (shared_memory_connected, broadcasting_connected)
        """
        # Conectar a Shared Memory
        shmem_connected = self.acc_telemetry.connect()
        
        # Conectar a Broadcasting si está habilitado
        broadcasting_connected = False
        if self.enable_broadcasting and shmem_connected:
            self.broadcasting_client = ACCBroadcastingClient()
            broadcasting_connected = self.broadcasting_client.connect(
                display_name="ACCRecorder",
                ip=self.broadcasting_config['ip'],
                port=self.broadcasting_config['port'],
                password=self.broadcasting_config['password'],
                command_password=self.broadcasting_config['command_password'],
                update_interval_ms=self.broadcasting_config['update_interval_ms']
            )
            
            if not broadcasting_connected:
                print("⚠️  Advertencia: No se pudo conectar al Broadcasting")
                print("   La telemetría se guardará sin datos de otros pilotos")
        
        # Notificar estado de conexión
        if self.on_connection_status:
            self.on_connection_status(shmem_connected, broadcasting_connected)
        
        return shmem_connected, broadcasting_connected
    
    def disconnect_from_acc(self):
        """Desconecta de Shared Memory y Broadcasting"""
        if self.broadcasting_client:
            self.broadcasting_client.disconnect()
            self.broadcasting_client = None
        
        self.acc_telemetry.disconnect()
    
    def start_recording(self, session_name: Optional[str] = None) -> Path:
        """
        Inicia la grabación de telemetría
        
        Args:
            session_name: Nombre personalizado para la sesión (opcional)
            
        Returns:
            Path al directorio de la sesión creada
        """
        if self.is_recording:
            raise RuntimeError("Ya existe una grabación en curso")
        
        # Conectar a ACC si no está conectado
        if not self.acc_telemetry.connected:
            shmem_ok, broadcast_ok = self.connect_to_acc()
            if not shmem_ok:
                raise RuntimeError("No se pudo conectar a ACC. Asegúrate de que el juego esté corriendo.")
        
        self.is_recording = True
        self.recording_start_time = datetime.now()
        self.telemetry_data = []
        
        # Crear nombre de sesión si no se proporciona
        if not session_name:
            session_name = self.recording_start_time.strftime("ACC_%Y%m%d_%H%M%S")
        
        # Crear directorio de sesión
        self.current_session_dir = self.output_dir / session_name
        self.current_session_dir.mkdir(exist_ok=True)
        
        # Guardar información inicial de sesión
        self._save_session_info()
        
        # Iniciar thread de grabación
        self.recording_thread = threading.Thread(
            target=self._recording_loop,
            daemon=True
        )
        self.recording_thread.start()
        
        # Notificar inicio
        if self.on_recording_started:
            self.on_recording_started(session_name)
        
        print(f"✅ Grabación iniciada: {session_name}")
        print(f"   Shared Memory: ✓")
        if self.broadcasting_client and self.broadcasting_client.connected:
            print(f"   Broadcasting: ✓ (posiciones de pilotos habilitadas)")
        else:
            print(f"   Broadcasting: ✗ (solo tu telemetría)")
        
        return self.current_session_dir
    
    def stop_recording(self, keep_data: bool = False) -> tuple[int, float]:
        """
        Detiene la grabación y guarda los datos
        
        Args:
            keep_data: Si es True, mantiene los datos en memoria después de guardar
        
        Returns:
            Tupla con (número de registros, duración en segundos)
        """
        if not self.is_recording:
            return 0, 0.0
        
        self.is_recording = False
        
        # Esperar a que termine el thread
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # Guardar telemetría
        records_count = len(self.telemetry_data)
        duration = 0.0
        
        if self.current_session_dir and self.telemetry_data:
            telemetry_file = self.current_session_dir / "telemetry.json"
            self._save_telemetry(telemetry_file)
            
            if self.recording_start_time:
                duration = (datetime.now() - self.recording_start_time).total_seconds()
            
            # Guardar resumen de sesión
            self._save_session_summary(records_count, duration)
            
            print(f"\n✅ Grabación finalizada:")
            print(f"   Registros: {records_count}")
            print(f"   Duración: {duration:.1f}s")
            print(f"   Guardado en: {self.current_session_dir}")
        
        # Notificar finalización
        if self.on_recording_stopped:
            self.on_recording_stopped(records_count, duration)
        
        # Limpiar (pero mantener datos si se solicita)
        if not keep_data:
            self.telemetry_data = []
        self.current_session_dir = None
        self.recording_start_time = None
        
        return records_count, duration
    
    def add_telemetry_record(self, data: Dict[str, Any]) -> None:
        """
        Añade un registro de telemetría
        
        Args:
            data: Diccionario con los datos de telemetría
        """
        if not self.is_recording:
            return
        
        # Añadir timestamp si no existe
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        self.telemetry_data.append(data)
        
        # Notificar actualización
        if self.on_telemetry_update:
            self.on_telemetry_update(data)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la grabación actual
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'is_recording': self.is_recording,
            'records_count': len(self.telemetry_data),
            'duration': 0.0,
            'session_dir': str(self.current_session_dir) if self.current_session_dir else None,
            'shared_memory_connected': self.acc_telemetry.connected,
            'broadcasting_connected': self.broadcasting_client.connected if self.broadcasting_client else False
        }
        
        if self.recording_start_time:
            stats['duration'] = (datetime.now() - self.recording_start_time).total_seconds()
        
        return stats
    
    def _recording_loop(self) -> None:
        """
        Loop principal de grabación que captura telemetría de ACC
        """
        sample_interval = 1.0 / self.sample_rate
        
        while self.is_recording:
            start_time = time.time()
            
            try:
                # Capturar telemetría completa
                telemetry_record = self._capture_telemetry()
                
                if telemetry_record:
                    self.add_telemetry_record(telemetry_record)
                
            except Exception as e:
                print(f"Error capturando telemetría: {e}")
            
            # Mantener frecuencia de muestreo
            elapsed = time.time() - start_time
            sleep_time = max(0, sample_interval - elapsed)
            time.sleep(sleep_time)
    
    def _capture_telemetry(self) -> Optional[Dict[str, Any]]:
        """
        Captura un frame completo de telemetría de ACC
        
        Returns:
            Diccionario con todos los datos de telemetría
        """
        if not self.acc_telemetry.connected:
            return None
        
        # Timestamp
        timestamp = datetime.now().isoformat()
        
        # Datos del jugador (Shared Memory)
        player_data = self.acc_telemetry.get_player_telemetry()
        session_info = self.acc_telemetry.get_session_info()
        car_info = self.acc_telemetry.get_car_info()
        
        # Datos de todos los pilotos (Broadcasting)
        standings = []
        track_data = {}
        broadcast_session = {}
        
        if self.broadcasting_client and self.broadcasting_client.connected:
            try:
                standings = self.broadcasting_client.get_standings()
                track_data = self.broadcasting_client.get_track_data()
                broadcast_session = self.broadcasting_client.get_session_info()
            except Exception as e:
                print(f"Error obteniendo datos de Broadcasting: {e}")
        
        # Construir registro completo
        record = {
            'timestamp': timestamp,
            'player_telemetry': player_data,
            'session_info': session_info,
            'car_info': car_info,
            'standings': standings,
            'track_data': track_data,
            'broadcast_session': broadcast_session
        }
        
        return record
    
    def _save_session_info(self) -> None:
        """Guarda información inicial de la sesión"""
        if not self.current_session_dir:
            return
        
        # Obtener información del coche y pista
        car_info = self.acc_telemetry.get_car_info()
        
        session_info_file = self.current_session_dir / "session_info.json"
        
        info = {
            'session_name': self.current_session_dir.name,
            'start_time': self.recording_start_time.isoformat(),
            'sample_rate': self.sample_rate,
            'broadcasting_enabled': self.enable_broadcasting and (self.broadcasting_client is not None),
            'car_info': car_info
        }
        
        with open(session_info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
    
    def _save_session_summary(self, records_count: int, duration: float) -> None:
        """Guarda resumen de la sesión"""
        if not self.current_session_dir:
            return
        
        summary_file = self.current_session_dir / "summary.json"
        
        summary = {
            'session_name': self.current_session_dir.name,
            'start_time': self.recording_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration,
            'records_count': records_count,
            'sample_rate': self.sample_rate,
            'broadcasting_enabled': self.enable_broadcasting and (self.broadcasting_client is not None)
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def _save_telemetry(self, filepath: Path) -> None:
        """
        Guarda los datos de telemetría en un archivo JSON
        
        Args:
            filepath: Ruta donde guardar el archivo
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.telemetry_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Error al guardar telemetría: {str(e)}")
    
    def load_telemetry(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Carga datos de telemetría desde un archivo
        
        Args:
            filepath: Ruta al archivo de telemetría
            
        Returns:
            Lista de registros de telemetría
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise IOError(f"Error al cargar telemetría: {str(e)}")
    
    def export_csv(self, filepath: Path, fields: Optional[List[str]] = None, 
                  data: Optional[List[Dict[str, Any]]] = None, flatten: bool = True) -> None:
        """
        Exporta la telemetría a formato CSV
        
        Args:
            filepath: Ruta donde guardar el CSV
            fields: Lista de campos a exportar (None = todos los campos planos)
            data: Datos a exportar (None = usar telemetry_data actual)
            flatten: Si True, aplana estructuras anidadas
        """
        import csv
        
        # Usar datos proporcionados o los datos actuales
        export_data = data if data is not None else self.telemetry_data
        
        if not export_data:
            raise ValueError("No hay datos de telemetría para exportar")
        
        # Aplanar datos si es necesario
        if flatten:
            flattened_data = [self._flatten_dict(record) for record in export_data]
        else:
            flattened_data = export_data
        
        # Determinar campos
        if not fields:
            # Usar todos los campos del primer registro
            fields = list(flattened_data[0].keys())
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for record in flattened_data:
                    row = {k: record.get(k, '') for k in fields}
                    writer.writerow(row)
        except Exception as e:
            raise IOError(f"Error al exportar CSV: {str(e)}")
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Aplana un diccionario anidado
        
        Args:
            d: Diccionario a aplanar
            parent_key: Clave padre para recursión
            sep: Separador para claves anidadas
            
        Returns:
            Diccionario plano
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Para listas, convertir a string o ignorar
                items.append((new_key, json.dumps(v) if v else ''))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def export_standings_csv(self, filepath: Path) -> None:
        """
        Exporta solo la clasificación a CSV
        
        Args:
            filepath: Ruta donde guardar el CSV
        """
        import csv
        
        if not self.telemetry_data:
            raise ValueError("No hay datos de telemetría")
        
        # Extraer todos los standings únicos
        all_standings = []
        for record in self.telemetry_data:
            standings = record.get('standings', [])
            if standings:
                for entry in standings:
                    entry_with_time = entry.copy()
                    entry_with_time['record_timestamp'] = record['timestamp']
                    all_standings.append(entry_with_time)
        
        if not all_standings:
            raise ValueError("No hay datos de clasificación en la telemetría")
        
        fields = ['record_timestamp', 'position', 'driver_name', 'car_number', 
                 'team_name', 'laps', 'delta']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for entry in all_standings:
                row = {k: entry.get(k, '') for k in fields}
                writer.writerow(row)
