"""
Configuración del ACC Race Recorder
"""

# Configuración de grabación
RECORDING_CONFIG = {
    # FFmpeg settings
    'video': {
        'framerate': 30,  # FPS de grabación
        'codec': 'libx264',  # Codec de video
        'preset': 'ultrafast',  # Preset de codificación (ultrafast, fast, medium, slow)
        'crf': 23,  # Calidad (0-51, menor = mejor calidad, 23 es buena calidad)
        'pixel_format': 'yuv420p'
    },
    
    # Telemetry settings
    'telemetry': {
        'sample_rate': 1,  # Segundos entre capturas (1 = cada segundo)
        'include_standings': True,  # Incluir clasificación
        'include_player_telemetry': True,  # Incluir telemetría del jugador
        'include_session_info': True  # Incluir info de sesión
    },
    
    # Monitoring settings
    'monitoring': {
        'check_interval': 2,  # Segundos entre verificaciones de ACC
        'auto_start_recording': True,  # Iniciar grabación automáticamente
        'auto_stop_on_finish': True  # Detener al finalizar carrera
    },
    
    # Output settings
    'output': {
        'base_directory': 'ACC_Recordings',  # Directorio base (relativo a HOME)
        'video_filename': 'race_recording.mp4',
        'telemetry_filename': 'telemetry.json',
        'session_folder_format': 'ACC_%Y%m%d_%H%M%S'  # Formato de carpeta por sesión
    }
}

# Procesos de ACC a monitorear
ACC_PROCESS_NAMES = [
    'AC2-Win64-Shipping.exe',  # Proceso principal de ACC
    'AC2.exe',
    'AssettoCorsa2.exe'
]

# Tipos de sesión que activan la grabación
RECORDABLE_SESSIONS = [
    'Practice',
    'Qualifying',
    'Race',
    'Hotlap',
    'Time Attack'
]
