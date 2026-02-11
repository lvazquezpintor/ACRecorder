"""
Módulo para la captura de pantalla con ffmpeg
"""

import subprocess
import threading
import time
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any


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
            'audio_bitrate': '128k'
        }
        
        # Callbacks
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[float], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
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
            # Iniciar proceso ffmpeg
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
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
    
    def _build_ffmpeg_command(self) -> list:
        """
        Construye el comando ffmpeg según la plataforma y configuración
        
        Returns:
            Lista con el comando y sus argumentos
        """
        system = platform.system()
        cmd = ['ffmpeg']
        
        # Configuración de entrada según plataforma
        if system == 'Windows':
            # Windows: captura con gdigrab
            cmd.extend([
                '-f', 'gdigrab',
                '-framerate', str(self.config['fps']),
                '-i', 'desktop'
            ])
            
            # Audio en Windows
            if self.config['audio']:
                cmd.extend([
                    '-f', 'dshow',
                    '-i', 'audio="Mezcla estéreo"'
                ])
                
        elif system == 'Darwin':  # macOS
            # macOS: captura con avfoundation
            cmd.extend([
                '-f', 'avfoundation',
                '-framerate', str(self.config['fps']),
                '-i', '1:0' if self.config['audio'] else '1'  # 1=pantalla, 0=audio
            ])
            
        else:  # Linux
            # Linux: captura con x11grab
            cmd.extend([
                '-f', 'x11grab',
                '-framerate', str(self.config['fps']),
                '-i', ':0.0'
            ])
            
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
            '-crf', str(self.config['crf'])
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
