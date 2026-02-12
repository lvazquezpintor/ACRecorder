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
        self.current_session_dir: Optional[Path] = None
        
        # Configuración por defecto
        self.config = {
            'fps': 30,
            'resolution': None,  # None = capturar resolución nativa
            'video_codec': 'libx264',  # Codec de video por defecto
            'hw_accel': None,  # Aceleración por hardware: 'nvenc', 'qsv', 'videotoolbox', None
            'preset': 'ultrafast',
            'crf': 23,
            'audio': True,
            'audio_device': None,  # None = autodetectar, o nombre específico del dispositivo
            'audio_codec': 'aac',
            'audio_bitrate': '128k',
            'pixel_format': 'yuv420p',
            'capture_cursor': True
        }
        
        # Callbacks
        self.on_recording_started: Optional[Callable[[str], None]] = None
        self.on_recording_stopped: Optional[Callable[[float], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Cache de dispositivos
        self._devices_cache: Optional[Dict[str, List[str]]] = None
        
        # Detectar capacidades de hardware
        self._detect_hardware_capabilities()
        
    def _detect_hardware_capabilities(self) -> None:
        """Detecta las capacidades de hardware disponibles"""
        system = platform.system()
        
        # Intentar detectar NVIDIA GPU para h264_nvenc
        if system == 'Windows' or system == 'Linux':
            try:
                result = subprocess.run(
                    ['ffmpeg', '-hide_banner', '-encoders'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                output = result.stdout.decode('utf-8', errors='ignore')
                
                if 'h264_nvenc' in output:
                    # NVIDIA GPU detectada
                    self.config['hw_accel'] = 'nvenc'
                    self.config['video_codec'] = 'h264_nvenc'
                elif 'h264_qsv' in output:
                    # Intel QuickSync detectado
                    self.config['hw_accel'] = 'qsv'
                    self.config['video_codec'] = 'h264_qsv'
            except Exception:
                pass
        
        elif system == 'Darwin':  # macOS
            # En macOS, usar VideoToolbox si está disponible
            try:
                result = subprocess.run(
                    ['ffmpeg', '-hide_banner', '-encoders'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                output = result.stdout.decode('utf-8', errors='ignore')
                
                if 'h264_videotoolbox' in output:
                    self.config['hw_accel'] = 'videotoolbox'
                    self.config['video_codec'] = 'h264_videotoolbox'
            except Exception:
                pass
    
    def configure(self, **kwargs) -> None:
        """
        Configura parámetros de grabación
        
        Args:
            fps: Frames por segundo (default: 30)
            resolution: Tupla (ancho, alto) o None para nativa
            video_codec: Codec de video (default: auto-detectado o libx264)
            hw_accel: Aceleración hardware ('nvenc', 'qsv', 'videotoolbox', None)
            preset: Preset de ffmpeg (default: ultrafast)
            crf: Constant Rate Factor, calidad (default: 23)
            audio: Capturar audio (default: True)
            audio_device: Dispositivo de audio específico o None para autodetectar
            audio_codec: Codec de audio (default: aac)
            audio_bitrate: Bitrate de audio (default: 128k)
            pixel_format: Formato de píxel (default: yuv420p)
            capture_cursor: Capturar cursor (default: True)
        """
        # Actualizar configuración
        self.config.update(kwargs)
        
        # Si se especifica hw_accel, ajustar el codec de video
        if 'hw_accel' in kwargs:
            hw_accel = kwargs['hw_accel']
            if hw_accel == 'nvenc':
                self.config['video_codec'] = 'h264_nvenc'
            elif hw_accel == 'qsv':
                self.config['video_codec'] = 'h264_qsv'
            elif hw_accel == 'videotoolbox':
                self.config['video_codec'] = 'h264_videotoolbox'
            elif hw_accel is None:
                self.config['video_codec'] = 'libx264'
    
    def start_recording(self, session_dir: Optional[Path] = None, output_filename: Optional[str] = None) -> Path:
        """
        Inicia la captura de pantalla
        
        Args:
            session_dir: Directorio de sesión donde guardar el video (opcional)
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
        
        # Determinar directorio de salida
        if session_dir:
            self.current_session_dir = Path(session_dir)
            self.current_session_dir.mkdir(exist_ok=True)
            output_dir = self.current_session_dir
        else:
            output_dir = self.output_dir
        
        # Generar nombre de archivo si no se proporciona
        if not output_filename:
            output_filename = self.recording_start_time.strftime("screen_%Y%m%d_%H%M%S.mp4")
        
        self.current_output_file = output_dir / output_filename
        
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
        self.current_session_dir = None
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
    
    def _get_audio_devices(self) -> List[str]:
        """
        Obtiene la lista de dispositivos de audio disponibles según la plataforma
        
        Returns:
            Lista de nombres de dispositivos de audio
        """
        if self._devices_cache:
            return self._devices_cache.get('audio', [])
        
        system = platform.system()
        audio_devices = []
        
        try:
            if system == 'Windows':
                # Listar dispositivos de audio en Windows (DirectShow)
                result = subprocess.run(
                    ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                
                output = result.stderr.decode('utf-8', errors='ignore')
                in_audio_section = False
                
                for line in output.split('\n'):
                    if 'DirectShow audio devices' in line:
                        in_audio_section = True
                    elif in_audio_section and ']  "' in line:
                        # Extraer nombre del dispositivo
                        parts = line.split('"')
                        if len(parts) >= 2:
                            device_name = parts[1]
                            audio_devices.append(device_name)
                    elif in_audio_section and 'DirectShow video devices' in line:
                        break
                        
            elif system == 'Darwin':  # macOS
                # Listar dispositivos de audio en macOS (AVFoundation)
                result = subprocess.run(
                    ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                
                output = result.stderr.decode('utf-8', errors='ignore')
                in_audio_section = False
                
                for line in output.split('\n'):
                    if 'AVFoundation audio devices:' in line:
                        in_audio_section = True
                    elif in_audio_section and '[AVFoundation' in line and ']' in line:
                        # Extraer nombre del dispositivo
                        device_name = line.split(']')[1].strip()
                        audio_devices.append(device_name)
                    elif in_audio_section and 'AVFoundation video devices:' in line:
                        break
                        
            else:  # Linux
                # Listar dispositivos de audio en Linux (PulseAudio/ALSA)
                result = subprocess.run(
                    ['pactl', 'list', 'sources', 'short'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                
                if result.returncode == 0:
                    output = result.stdout.decode('utf-8', errors='ignore')
                    for line in output.split('\n'):
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                audio_devices.append(parts[1])
                else:
                    # Fallback a ALSA
                    audio_devices = ['default', 'hw:0', 'pulse']
            
            self._devices_cache = {'audio': audio_devices}
            return audio_devices
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error obteniendo dispositivos de audio: {str(e)}")
            return []
    
    def _get_default_audio_device(self) -> Optional[str]:
        """
        Obtiene el dispositivo de audio por defecto del sistema
        
        Returns:
            Nombre del dispositivo de audio por defecto o None
        """
        system = platform.system()
        
        if system == 'Windows':
            # En Windows, buscar dispositivo de mezcla estéreo o similar
            devices = self._get_audio_devices()
            
            # Prioridad de búsqueda
            priority_keywords = [
                'Mezcla estéreo',
                'Stereo Mix',
                'CABLE Output',
                'Wave Out Mix',
                'What U Hear',
                'Loopback'
            ]
            
            # Buscar por orden de prioridad
            for keyword in priority_keywords:
                for device in devices:
                    if keyword.lower() in device.lower():
                        return device
            
            # Si no se encuentra, usar el primer dispositivo disponible
            return devices[0] if devices else None
            
        elif system == 'Darwin':  # macOS
            # En macOS, el índice 0 suele ser el dispositivo de entrada por defecto
            return '0'
            
        else:  # Linux
            # En Linux, 'default' suele apuntar al dispositivo correcto
            return 'default'
    
    def _get_macos_screen_index(self) -> str:
        """
        Obtiene el índice de captura de pantalla para macOS
        
        Returns:
            String con el índice de captura (ej: "0", "1", "Capture screen 0")
        """
        devices = self._get_audio_devices()
        
        # En macOS, el dispositivo de pantalla suele ser el índice 1
        # pero puede variar según la configuración
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
            # Windows: captura con gdigrab o dxgi
            if self.config.get('hw_accel') == 'nvenc':
                # Usar d3d11grab para mejor rendimiento con NVIDIA
                cmd.extend([
                    '-f', 'gdigrab',
                    '-framerate', str(self.config['fps']),
                ])
            else:
                cmd.extend([
                    '-f', 'gdigrab',
                    '-framerate', str(self.config['fps']),
                ])
            
            if self.config['capture_cursor']:
                cmd.extend(['-draw_mouse', '1'])
            
            cmd.extend(['-i', 'desktop'])
            
            # Audio en Windows
            if self.config['audio']:
                audio_device = self.config.get('audio_device') or self._get_default_audio_device()
                if audio_device:
                    cmd.extend([
                        '-f', 'dshow',
                        '-i', f'audio={audio_device}'
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
                audio_device = self.config.get('audio_device') or self._get_default_audio_device()
                if audio_device:
                    cmd.extend(['-i', f"{screen_index}:{audio_device}"])
                else:
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
                audio_device = self.config.get('audio_device') or self._get_default_audio_device()
                if audio_device:
                    cmd.extend([
                        '-f', 'pulse',
                        '-i', audio_device
                    ])
        
        # Configuración de video
        video_codec = self.config['video_codec']
        cmd.extend(['-c:v', video_codec])
        
        # Preset (no todos los codecs lo soportan)
        if video_codec in ['libx264', 'libx265']:
            cmd.extend(['-preset', self.config['preset']])
        elif video_codec == 'h264_nvenc':
            # NVENC tiene sus propios presets
            nvenc_preset = 'p4'  # Equivalente a 'fast'
            if self.config['preset'] == 'ultrafast':
                nvenc_preset = 'p1'
            elif self.config['preset'] == 'medium':
                nvenc_preset = 'p5'
            cmd.extend(['-preset', nvenc_preset])
        
        # CRF o calidad
        if video_codec in ['libx264', 'libx265']:
            cmd.extend(['-crf', str(self.config['crf'])])
        elif video_codec == 'h264_nvenc':
            # NVENC usa -cq en lugar de -crf
            cmd.extend(['-cq', str(self.config['crf'])])
        
        # Formato de píxel
        cmd.extend(['-pix_fmt', self.config['pixel_format']])
        
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
    
    def list_audio_devices(self) -> List[str]:
        """
        Lista los dispositivos de audio disponibles
        
        Returns:
            Lista de nombres de dispositivos de audio
        """
        return self._get_audio_devices()
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre las capacidades de hardware
        
        Returns:
            Diccionario con información de hardware
        """
        return {
            'hw_accel': self.config.get('hw_accel'),
            'video_codec': self.config.get('video_codec'),
            'system': platform.system()
        }
    
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
