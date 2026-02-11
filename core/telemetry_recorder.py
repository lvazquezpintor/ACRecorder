"""
Módulo para la grabación de telemetría de ACC
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional


class TelemetryRecorder:
    """Gestiona la grabación de datos de telemetría"""
    
    def __init__(self, output_dir: Path):
        """
        Inicializa el grabador de telemetría
        
        Args:
            output_dir: Directorio base donde se guardarán las sesiones
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.telemetry_data: List[Dict[str, Any]] = []
        self.current_session_dir: Optional[Path] = None
        self.recording_start_time: Optional[datetime] = None
        
        # Callbacks
        self.on_telemetry_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[int, float], None]] = None
        
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
        
        self.is_recording = True
        self.recording_start_time = datetime.now()
        self.telemetry_data = []
        
        # Crear nombre de sesión si no se proporciona
        if not session_name:
            session_name = self.recording_start_time.strftime("ACC_%Y%m%d_%H%M%S")
        
        # Crear directorio de sesión
        self.current_session_dir = self.output_dir / session_name
        self.current_session_dir.mkdir(exist_ok=True)
        
        # Iniciar thread de grabación
        self.recording_thread = threading.Thread(
            target=self._recording_loop,
            daemon=True
        )
        self.recording_thread.start()
        
        # Notificar inicio
        if self.on_recording_started:
            self.on_recording_started(session_name)
        
        return self.current_session_dir
    
    def stop_recording(self) -> tuple[int, float]:
        """
        Detiene la grabación y guarda los datos
        
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
        
        # Notificar finalización
        if self.on_recording_stopped:
            self.on_recording_stopped(records_count, duration)
        
        # Limpiar
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
            'session_dir': str(self.current_session_dir) if self.current_session_dir else None
        }
        
        if self.recording_start_time:
            stats['duration'] = (datetime.now() - self.recording_start_time).total_seconds()
        
        return stats
    
    def _recording_loop(self) -> None:
        """
        Loop principal de grabación (ejecutado en thread separado)
        Este método puede ser extendido para leer datos de telemetría
        de forma continua desde una fuente externa
        """
        while self.is_recording:
            # Aquí iría la lógica para leer datos de telemetría
            # Por ahora solo esperamos
            time.sleep(0.1)
    
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
    
    def export_csv(self, filepath: Path, fields: Optional[List[str]] = None) -> None:
        """
        Exporta la telemetría actual a formato CSV
        
        Args:
            filepath: Ruta donde guardar el CSV
            fields: Lista de campos a exportar (None = todos)
        """
        if not self.telemetry_data:
            raise ValueError("No hay datos de telemetría para exportar")
        
        import csv
        
        # Determinar campos
        if not fields:
            fields = list(self.telemetry_data[0].keys())
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for record in self.telemetry_data:
                    row = {k: record.get(k, '') for k in fields}
                    writer.writerow(row)
        except Exception as e:
            raise IOError(f"Error al exportar CSV: {str(e)}")
