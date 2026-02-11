"""
Módulo para detectar y gestionar el estado de sesiones de ACC

Este módulo monitorea el estado de ACC y detecta cuando una sesión/carrera
realmente comienza usando el tiempo de sesión de ACC.
"""

import time
import threading
from typing import Optional, Callable
from datetime import datetime
from enum import Enum


class SessionStatus(Enum):
    """Estados posibles de una sesión de ACC"""
    UNKNOWN = 0
    OFF = 1           # ACC cerrado o no conectado
    MENU = 2          # En menús
    REPLAY = 3        # Viendo replay
    LIVE_PAUSED = 4   # Sesión en pausa
    LIVE_WAITING = 5  # En pits esperando/calentamiento (tiempo = 0)
    LIVE_RACING = 6   # Corriendo activamente (tiempo > 0)


class ACCSessionMonitor:
    """
    Monitorea el estado de las sesiones de ACC y detecta cuándo
    comienza y termina una carrera usando el tiempo de sesión
    """
    
    def __init__(self, telemetry_reader):
        """
        Inicializa el monitor de sesiones
        
        Args:
            telemetry_reader: Instancia de ACCTelemetry para leer datos
        """
        self.telemetry = telemetry_reader
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Estado actual
        self.current_status = SessionStatus.UNKNOWN
        self.session_type: Optional[str] = None
        self.is_in_race = False
        self.race_started_time: Optional[datetime] = None
        
        # Configuración de detección
        self.config = {
            'min_session_time_ms': 100,    # Tiempo mínimo de sesión para considerar inicio (ms)
            'update_interval': 0.5,        # Frecuencia de polling (segundos)
            'time_check_duration': 2.0,    # Segundos confirmando tiempo > 0
        }
        
        # Callbacks
        self.on_race_started: Optional[Callable[[dict], None]] = None
        self.on_race_ended: Optional[Callable[[dict], None]] = None
        self.on_status_changed: Optional[Callable[[SessionStatus, SessionStatus], None]] = None
        
        # Variables de detección
        self._session_time_positive_since: Optional[float] = None
        self._last_session_time_ms = 0
        
    def configure(self, **kwargs) -> None:
        """
        Configura parámetros de detección
        
        Args:
            min_session_time_ms: Tiempo mínimo de sesión para inicio (ms)
            update_interval: Frecuencia de polling (segundos)
            time_check_duration: Tiempo confirmando session_time > 0 (segundos)
        """
        self.config.update(kwargs)
    
    def start_monitoring(self) -> bool:
        """
        Inicia el monitoreo de sesiones
        
        Returns:
            True si se inició correctamente, False en caso contrario
        """
        if self.is_monitoring:
            return True
        
        # Intentar conectar con ACC
        if not self.telemetry.connect():
            return False
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        return True
    
    def stop_monitoring(self) -> None:
        """Detiene el monitoreo de sesiones"""
        self.is_monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        self.telemetry.disconnect()
    
    def _monitoring_loop(self) -> None:
        """Loop principal de monitoreo (ejecuta en thread separado)"""
        while self.is_monitoring:
            try:
                self._check_session_state()
                time.sleep(self.config['update_interval'])
            except Exception as e:
                print(f"Error en monitoring loop: {e}")
                time.sleep(1.0)
    
    def _check_session_state(self) -> None:
        """Verifica el estado actual de la sesión"""
        # Obtener información de sesión
        session_info = self.telemetry.get_session_info()
        
        if not session_info:
            self._update_status(SessionStatus.OFF)
            return
        
        # Determinar estado basado en datos
        status_str = session_info.get('status', 'Off')
        session_time_ms = session_info.get('current_time_ms', 0)
        
        # Determinar nuevo estado
        new_status = self._determine_status(status_str, session_time_ms, session_info)
        
        # Detectar inicio/fin de carrera basándose en session_time
        self._detect_race_transitions(new_status, session_time_ms, session_info)
        
        # Actualizar estado
        self._update_status(new_status)
        
        # Guardar último tiempo de sesión
        self._last_session_time_ms = session_time_ms
    
    def _determine_status(self, status_str: str, session_time_ms: int, 
                         session_info: dict) -> SessionStatus:
        """
        Determina el estado de la sesión basándose en los datos
        
        Args:
            status_str: Estado reportado por ACC ('Off', 'Live', 'Replay', 'Pause')
            session_time_ms: Tiempo de sesión actual en milisegundos
            session_info: Información completa de la sesión
            
        Returns:
            SessionStatus correspondiente
        """
        if status_str == 'Off':
            return SessionStatus.OFF
        
        if status_str == 'Replay':
            return SessionStatus.REPLAY
        
        if status_str == 'Pause':
            return SessionStatus.LIVE_PAUSED
        
        if status_str == 'Live':
            # Determinar si está corriendo o esperando basándose en session_time
            # session_time_ms > 0 significa que la sesión ha comenzado
            if session_time_ms > self.config['min_session_time_ms']:
                return SessionStatus.LIVE_RACING
            else:
                return SessionStatus.LIVE_WAITING
        
        return SessionStatus.UNKNOWN
    
    def _detect_race_transitions(self, new_status: SessionStatus, 
                                 session_time_ms: int, session_info: dict) -> None:
        """
        Detecta cuando comienza o termina una carrera basándose en session_time
        
        Args:
            new_status: Nuevo estado detectado
            session_time_ms: Tiempo de sesión en milisegundos
            session_info: Información de la sesión
        """
        # Detectar INICIO de carrera
        # Método nuevo: Usar session_time en lugar de velocidad
        if new_status == SessionStatus.LIVE_RACING and not self.is_in_race:
            # Verificar que el session_time sea positivo y se mantenga
            current_time = time.time()
            
            if session_time_ms > self.config['min_session_time_ms']:
                if self._session_time_positive_since is None:
                    self._session_time_positive_since = current_time
                elif (current_time - self._session_time_positive_since) >= self.config['time_check_duration']:
                    # ¡La carrera ha comenzado!
                    self._start_race(session_info)
            else:
                self._session_time_positive_since = None
        
        # Detectar FIN de carrera
        elif self.is_in_race and new_status in [SessionStatus.OFF, SessionStatus.MENU, SessionStatus.REPLAY]:
            self._end_race(session_info)
        
        # También detectar si session_time vuelve a 0 (nueva sesión)
        elif self.is_in_race and session_time_ms == 0 and self._last_session_time_ms > 0:
            # El tiempo volvió a 0, probablemente se reinició la sesión
            self._end_race(session_info)
        
        # Resetear contador si no está corriendo
        if new_status != SessionStatus.LIVE_RACING:
            self._session_time_positive_since = None
    
    def _start_race(self, session_info: dict) -> None:
        """
        Marca el inicio de una carrera
        
        Args:
            session_info: Información de la sesión cuando comenzó
        """
        if self.is_in_race:
            return
        
        self.is_in_race = True
        self.race_started_time = datetime.now()
        self.session_type = session_info.get('session_type', 'Unknown')
        
        race_data = {
            'session_type': self.session_type,
            'started_at': self.race_started_time,
            'session_time_ms': session_info.get('current_time_ms', 0),
            'session_info': session_info
        }
        
        # Notificar callbacks
        if self.on_race_started:
            self.on_race_started(race_data)
    
    def _end_race(self, session_info: dict) -> None:
        """
        Marca el fin de una carrera
        
        Args:
            session_info: Información de la sesión cuando terminó
        """
        if not self.is_in_race:
            return
        
        duration = None
        if self.race_started_time:
            duration = (datetime.now() - self.race_started_time).total_seconds()
        
        race_data = {
            'session_type': self.session_type,
            'started_at': self.race_started_time,
            'ended_at': datetime.now(),
            'duration_seconds': duration,
            'final_session_time_ms': session_info.get('current_time_ms', 0),
            'session_info': session_info
        }
        
        # Notificar callbacks
        if self.on_race_ended:
            self.on_race_ended(race_data)
        
        # Reset
        self.is_in_race = False
        self.race_started_time = None
        self.session_type = None
    
    def _update_status(self, new_status: SessionStatus) -> None:
        """
        Actualiza el estado y notifica si cambió
        
        Args:
            new_status: Nuevo estado detectado
        """
        if new_status != self.current_status:
            old_status = self.current_status
            self.current_status = new_status
            
            # Notificar cambio de estado
            if self.on_status_changed:
                self.on_status_changed(old_status, new_status)
    
    def get_current_state(self) -> dict:
        """
        Obtiene el estado actual del monitor
        
        Returns:
            Diccionario con información del estado actual
        """
        return {
            'is_monitoring': self.is_monitoring,
            'current_status': self.current_status.name,
            'is_in_race': self.is_in_race,
            'session_type': self.session_type,
            'race_started_time': self.race_started_time.isoformat() if self.race_started_time else None,
            'race_duration': (datetime.now() - self.race_started_time).total_seconds() if self.race_started_time else None,
            'last_session_time_ms': self._last_session_time_ms
        }
