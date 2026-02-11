"""
Módulo para la captura de pantalla con ffmpeg
"""

import subprocess
import threading
import time
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List


class ScreenRecorder:
    """Gestiona la captura de pantalla usando ffmpeg"""
    
    def __init__(self, output_dir: Path):
        """
        Inicializa el grabador de pantalla
        
        Args:
            output_dir: Directorio base donde se guardarán las grabaciones
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.is_recording = False
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.current_output_file: Optional[Path] = None
        self.recording_start_time: Optional[datetime] = None
        
        # Configuración por defecto
        self.config = {
            'fps': 30,
            'resolution': None,  # None = capturar resolución nativa
            'codec': 'libx264',
            'preset': 'ultrafast',
            'crf': 23,
            'audio': True,
            'audio_codec': 'aac',
            'audio_bitrate': '128k',
            'pixel_format': 'yuv420p',  # Compatibilidad con reproductores
            'capture_cursor': True  # Capturar cursor del mouse
        }
        
        # Callbacks
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[float], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Cache de dispositivos para macOS
        self._macos_devices_cache: Optional[Dict[str, List[str]]] = None
        
    def configure(self, **kwargs) -> None:
        """
        Configura parámetros de grabación
        
        Args:
            fps: Frames por segundo (default: 30)
            resolution: Tupla (ancho, alto) o None para nativa
            codec: Codec de video (default: libx264)
            preset: Preset de ffmpeg (default: ultrafast)
            crf: Constant Rate Factor, calidad (default: 23)
            audio: Capturar audio (default: True)
            audio_codec: Codec de audio (default: aac)
            audio_bitrate: Bitrate de audio (default: 128k)
            pixel_format: Formato de píxel (default: yuv420p)
            capture_cursor: Capturar cursor (default: True)
        """
        self.config.update(kwargs)
    
    def start_recording(self, output_filename: Optional[str] = None) -> Path:
        """
        Inicia la captura de pantalla
        
        Args:
            output_filename: Nombre del archivo de salida (opcional)
            
        Returns:
            Path al archivo de video que se está grabando
        """
        if self.is_recording:
            raise RuntimeError("Ya existe una grabación en curso")
        
        # Verificar que ffmpeg está disponible
        if not self._check_ffmpeg():
            error_msg = "ffmpeg no está instalado o no está en el PATH"
            if self.on_error:
                self.on_error(error_msg)
            raise RuntimeError(error_msg)
        
        self.recording_start_time = datetime.now()
        
        # Generar nombre de archivo si no se proporciona
        if not output_filename:
            output_filename = self.recording_start_time.strftime("screen_%Y%m%d_%H%M%S.mp4")
        
        self.current_output_file = self.output_dir / output_filename
        
        # Construir comando ffmpeg según la plataforma
        cmd = self._build_ffmpeg_command()
        
        try:
            # Log del comando para debugging
            if self.on_error:
                self.on_error(f"DEBUG: Ejecutando comando: {' '.join(cmd)}")
            
            # Iniciar proceso ffmpeg
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            # Dar tiempo a ffmpeg para iniciar y detectar errores inmediatos
            time.sleep(0.5)
            
            # Verificar si el proceso sigue vivo
            if self.ffmpeg_process.poll() is not None:
                # El proceso terminó inmediatamente - hay un error
                stderr = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                error_msg = f"ffmpeg falló al iniciar: {stderr[-1000:]}"
                if self.on_error:
                    self.on_error(error_msg)
                raise RuntimeError(error_msg)
            
            self.is_recording = True
            
            # Iniciar thread para monitorear el proceso
            monitor_thread = threading.Thread(
                target=self._monitor_ffmpeg,
                daemon=True
            )
            monitor_thread.start()
            
            # Notificar inicio
            if self.on_recording_started:
                self.on_recording_started(str(self.current_output_file))
            
            return self.current_output_file
            
        except Exception as e:
            error_msg = f"Error al iniciar ffmpeg: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            raise RuntimeError(error_msg)
    
    def stop_recording(self) -> Optional[float]:
        """
        Detiene la captura de pantalla
        
        Returns:
            Duración de la grabación en segundos, o None si no había grabación
        """
        if not self.is_recording or not self.ffmpeg_process:
            return None
        
        duration = None
        if self.recording_start_time:
            duration = (datetime.now() - self.recording_start_time).total_seconds()
        
        try:
            # Enviar señal de terminación a ffmpeg (q para quit)
            if platform.system() == 'Darwin':
                # En macOS, usar SIGINT es más confiable
                self.ffmpeg_process.send_signal(subprocess.signal.SIGINT)
                self.ffmpeg_process.wait(timeout=5)
            else:
                self.ffmpeg_process.communicate(input=b'q', timeout=5)
        except subprocess.TimeoutExpired:
            # Si no responde, forzar terminación
            self.ffmpeg_process.kill()
            self.ffmpeg_process.wait()
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error al detener ffmpeg: {str(e)}")
        
        self.is_recording = False
        self.ffmpeg_process = None
        
        # Notificar finalización
        if self.on_recording_stopped and duration:
            self.on_recording_stopped(duration)
        
        # Limpiar
        output_file = self.current_output_file
        self.current_output_file = None
        self.recording_start_time = None
        
        return duration
    
    def get_current_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la grabación actual
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'is_recording': self.is_recording,
            'duration': 0.0,
            'output_file': str(self.current_output_file) if self.current_output_file else None
        }
        
        if self.recording_start_time:
            stats['duration'] = (datetime.now() - self.recording_start_time).total_seconds()
        
        return stats
    
    def _check_ffmpeg(self) -> bool:
        """
        Verifica que ffmpeg esté disponible
        
        Returns:
            True si ffmpeg está disponible, False en caso contrario
        """
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _get_macos_devices(self) -> Dict[str, List[str]]:
        """
        Obtiene la lista de dispositivos disponibles en macOS
        
        Returns:
            Diccionario con listas de dispositivos de video y audio
        """
        if self._macos_devices_cache:
            return self._macos_devices_cache
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            
            output = result.stderr.decode('utf-8', errors='ignore')
            
            video_devices = []
            audio_devices = []
            current_section = None
            
            for line in output.split('\n'):
                if 'AVFoundation video devices:' in line:
                    current_section = 'video'
                elif 'AVFoundation audio devices:' in line:
                    current_section = 'audio'
                elif current_section and '[AVFoundation' in line and ']' in line:
                    # Extraer nombre del dispositivo
                    device_name = line.split(']')[1].strip()
                    if current_section == 'video':
                        video_devices.append(device_name)
                    elif current_section == 'audio':
                        audio_devices.append(device_name)
            
            self._macos_devices_cache = {
                'video': video_devices,
                'audio': audio_devices
            }
            
            return self._macos_devices_cache
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error obteniendo dispositivos macOS: {str(e)}")
            return {'video': [], 'audio': []}
    
    def _get_macos_screen_index(self) -> str:
        """
        Obtiene el índice de captura de pantalla para macOS
        
        Returns:
            String con el índice de captura (ej: "0", "1", "Capture screen 0")
        """
        devices = self._get_macos_devices()
        
        # Buscar dispositivo de captura de pantalla
        for i, device in enumerate(devices['video']):
            if 'Capture screen' in device or 'Screen' in device:
                return str(i)
        
        # Si no se encuentra, intentar con índice 1 (valor común)
        return "1"
    
    def _build_ffmpeg_command(self) -> list:
        """
        Construye el comando ffmpeg según la plataforma y configuración
        
        Returns:
            Lista con el comando y sus argumentos
        """
        system = platform.system()
        cmd = ['ffmpeg']
        
        # Sobrescribir archivo sin preguntar
        cmd.append('-y')
        
        # Configuración de entrada según plataforma
        if system == 'Windows':
            # Windows: captura con gdigrab
            cmd.extend([
                '-f', 'gdigrab',
                '-framerate', str(self.config['fps']),
            ])
            
            if self.config['capture_cursor']:
                cmd.extend(['-draw_mouse', '1'])
            
            cmd.extend(['-i', 'desktop'])
            
            # Audio en Windows
            if self.config['audio']:
                cmd.extend([
                    '-f', 'dshow',
                    '-i', 'audio="Mezcla estéreo"'
                ])
                
        elif system == 'Darwin':  # macOS
            # Obtener índice de pantalla
            screen_index = self._get_macos_screen_index()
            
            # Opciones de captura para macOS
            cmd.extend(['-f', 'avfoundation'])
            
            # Framerate
            cmd.extend(['-framerate', str(self.config['fps'])])
            
            # Capturar cursor
            if self.config['capture_cursor']:
                cmd.extend(['-capture_cursor', '1'])
            
            # Capturar clicks del mouse
            cmd.extend(['-capture_mouse_clicks', '1'])
            
            # Dispositivo de entrada (pantalla:audio)
            if self.config['audio']:
                # Intentar obtener dispositivo de audio
                devices = self._get_macos_devices()
                if devices['audio']:
                    # Usar primer dispositivo de audio disponible
                    cmd.extend(['-i', f"{screen_index}:0"])
                else:
                    # Sin audio si no hay dispositivos
                    cmd.extend(['-i', screen_index])
            else:
                cmd.extend(['-i', screen_index])
            
        else:  # Linux
            # Linux: captura con x11grab
            cmd.extend([
                '-f', 'x11grab',
                '-framerate', str(self.config['fps']),
            ])
            
            if self.config['capture_cursor']:
                cmd.extend(['-draw_mouse', '1'])
            
            cmd.extend(['-i', ':0.0'])
            
            # Audio en Linux
            if self.config['audio']:
                cmd.extend([
                    '-f', 'pulse',
                    '-i', 'default'
                ])
        
        # Configuración de video
        cmd.extend([
            '-c:v', self.config['codec'],
            '-preset', self.config['preset'],
            '-crf', str(self.config['crf']),
            '-pix_fmt', self.config['pixel_format']
        ])
        
        # Resolución si se especifica
        if self.config['resolution']:
            width, height = self.config['resolution']
            cmd.extend(['-s', f'{width}x{height}'])
        
        # Configuración de audio
        if self.config['audio']:
            cmd.extend([
                '-c:a', self.config['audio_codec'],
                '-b:a', self.config['audio_bitrate']
            ])
        
        # Archivo de salida
        cmd.append(str(self.current_output_file))
        
        return cmd
    
    def _monitor_ffmpeg(self) -> None:
        """
        Monitorea el proceso ffmpeg para detectar errores
        """
        if not self.ffmpeg_process:
            return
        
        while self.is_recording and self.ffmpeg_process:
            # Verificar si el proceso sigue vivo
            if self.ffmpeg_process.poll() is not None:
                # El proceso terminó
                self.is_recording = False
                
                # Leer stderr para obtener información del error
                if self.ffmpeg_process.stderr:
                    stderr = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                    if stderr and self.on_error:
                        self.on_error(f"ffmpeg terminó inesperadamente: {stderr[-500:]}")
                
                break
            
            time.sleep(1)
    
    def list_macos_devices(self) -> Dict[str, List[str]]:
        """
        Lista los dispositivos disponibles en macOS
        
        Returns:
            Diccionario con listas de dispositivos de video y audio
        """
        if platform.system() != 'Darwin':
            return {'video': [], 'audio': []}
        
        return self._get_macos_devices()
    
    def get_video_info(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """
        Obtiene información sobre un archivo de video usando ffprobe
        
        Args:
            video_path: Ruta al archivo de video
            
        Returns:
            Diccionario con información del video o None si hay error
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                return json.loads(result.stdout.decode('utf-8'))
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error al obtener info del video: {str(e)}")
        
        return None
