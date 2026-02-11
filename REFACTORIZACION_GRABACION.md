# Refactorización de Grabación de Telemetría y Pantalla

## Resumen de Cambios

Se ha refactorizado la lógica de grabación de telemetría y captura de pantalla, extrayéndola desde `main_window.py` a módulos independientes en la carpeta `core/`, siguiendo los principios de separación de responsabilidades y arquitectura modular.

## Nuevos Módulos Creados

### 1. `core/telemetry_recorder.py`

**Responsabilidad**: Gestionar la grabación, almacenamiento y exportación de datos de telemetría.

**Características principales**:
- ✅ Grabación en formato JSON
- ✅ Sistema de callbacks para eventos (inicio, fin, actualización)
- ✅ Gestión automática de timestamps
- ✅ Exportación a CSV
- ✅ Carga de telemetría existente
- ✅ Estadísticas en tiempo real
- ✅ Thread-safe (grabación en thread separado)

**API principal**:
```python
# Inicializar
recorder = TelemetryRecorder(output_dir)

# Configurar callbacks
recorder.on_recording_started = lambda name: print(f"Started: {name}")
recorder.on_recording_stopped = lambda count, duration: print(f"Stopped: {count} records")
recorder.on_telemetry_update = lambda data: print(f"New data: {data}")

# Iniciar grabación
session_dir = recorder.start_recording(session_name="mi_sesion")

# Añadir datos
recorder.add_telemetry_record({
    'speed': 120.5,
    'rpm': 8500,
    'gear': 4
})

# Obtener estadísticas
stats = recorder.get_current_stats()

# Detener grabación (guarda automáticamente)
records, duration = recorder.stop_recording()

# Exportar a CSV
recorder.export_csv(Path("output.csv"), fields=['speed', 'rpm'])
```

### 2. `core/screen_recorder.py`

**Responsabilidad**: Gestionar la captura de pantalla usando ffmpeg.

**Características principales**:
- ✅ Soporte multiplataforma (Windows, macOS, Linux)
- ✅ Configuración flexible (fps, codec, calidad, audio)
- ✅ Detección automática de ffmpeg
- ✅ Sistema de callbacks para eventos y errores
- ✅ Monitoreo del proceso ffmpeg
- ✅ Finalización segura del proceso
- ✅ Obtención de información de videos (ffprobe)

**Configuración por plataforma**:
- **Windows**: `gdigrab` para video, `dshow` para audio
- **macOS**: `avfoundation`
- **Linux**: `x11grab` para video, `pulse` para audio

**API principal**:
```python
# Inicializar
recorder = ScreenRecorder(output_dir)

# Configurar parámetros
recorder.configure(
    fps=60,
    resolution=(1920, 1080),  # None para nativa
    codec='libx264',
    preset='fast',
    crf=20,
    audio=True
)

# Configurar callbacks
recorder.on_recording_started = lambda path: print(f"Recording to: {path}")
recorder.on_recording_stopped = lambda duration: print(f"Duration: {duration}s")
recorder.on_error = lambda msg: print(f"Error: {msg}")

# Iniciar grabación
output_file = recorder.start_recording("gameplay.mp4")

# Obtener estadísticas
stats = recorder.get_current_stats()

# Detener grabación
duration = recorder.stop_recording()

# Obtener información de video
info = recorder.get_video_info(Path("video.mp4"))
```

### 3. Actualización de `core/__init__.py`

```python
from .telemetry_recorder import TelemetryRecorder
from .screen_recorder import ScreenRecorder

__all__ = ['TelemetryRecorder', 'ScreenRecorder']
```

## Cambios en `gui/main_window.py`

### Antes (código acoplado)
```python
class MainWindow:
    def __init__(self):
        self.is_recording = False
        self.telemetry_data = []
        self.ffmpeg_process = None
        # ... lógica mezclada con UI
    
    def start_recording(self):
        # Lógica de negocio mezclada
        self.telemetry_data = []
        # Iniciar ffmpeg manualmente
        # ...
    
    def stop_recording(self):
        # Guardar telemetría manualmente
        import json
        with open(...) as f:
            json.dump(...)
        # Detener ffmpeg manualmente
        # ...
```

### Después (código desacoplado)
```python
class MainWindow:
    def __init__(self):
        # Inicializar grabadores
        self.telemetry_recorder = TelemetryRecorder(self.output_dir)
        self.screen_recorder = ScreenRecorder(self.output_dir)
        
        # Configurar callbacks
        self.telemetry_recorder.on_recording_started = self._on_telemetry_started
        self.screen_recorder.on_recording_started = self._on_screen_started
        # ...
    
    def start_recording(self):
        session_name = datetime.now().strftime("ACC_%Y%m%d_%H%M%S")
        self.telemetry_recorder.start_recording(session_name)
        self.screen_recorder.start_recording(f"{session_name}.mp4")
    
    def stop_recording(self):
        self.screen_recorder.stop_recording()
        self.telemetry_recorder.stop_recording()
```

## Ventajas de la Refactorización

### 1. **Separación de Responsabilidades**
- ✅ La GUI solo gestiona la interfaz de usuario
- ✅ La lógica de negocio está en módulos `core`
- ✅ Cada módulo tiene una responsabilidad única y bien definida

### 2. **Reusabilidad**
- ✅ Los grabadores pueden usarse en otros proyectos
- ✅ Se pueden usar independientemente (solo telemetría, solo pantalla)
- ✅ Fácil integración en aplicaciones CLI o servidores

### 3. **Testabilidad**
- ✅ Los módulos core se pueden testear sin GUI
- ✅ Inyección de dependencias mediante callbacks
- ✅ Código más fácil de mockear para unit tests

### 4. **Mantenibilidad**
- ✅ Cambios en la lógica de grabación no afectan a la GUI
- ✅ Código más limpio y fácil de entender
- ✅ Mejor organización del proyecto

### 5. **Extensibilidad**
- ✅ Fácil añadir nuevas funcionalidades (ej: streaming)
- ✅ Sistema de callbacks permite múltiples consumidores
- ✅ Configuración flexible sin modificar código

### 6. **Gestión de Errores**
- ✅ Manejo de errores centralizado
- ✅ Callbacks de error para notificar a la UI
- ✅ Validaciones en la capa de negocio

## Estructura del Proyecto

```
ACRecorder/
├── core/
│   ├── __init__.py              # Exporta TelemetryRecorder y ScreenRecorder
│   ├── telemetry_recorder.py   # ✨ NUEVO - Grabación de telemetría
│   └── screen_recorder.py       # ✨ NUEVO - Captura de pantalla
├── gui/
│   ├── main_window.py           # ♻️ REFACTORIZADO - Usa módulos core
│   ├── widgets.py
│   ├── tabs.py
│   └── styles.py
└── ...
```

## Flujo de Grabación Refactorizado

```
Usuario presiona "Start Monitoring"
    ↓
MainWindow.start_monitoring()
    ↓
Thread de monitoreo detecta ACC
    ↓
MainWindow.start_recording()
    ├─→ TelemetryRecorder.start_recording()
    │       ├─→ Crea directorio de sesión
    │       ├─→ Inicia thread de grabación
    │       └─→ Callback: _on_telemetry_started()
    │
    └─→ ScreenRecorder.start_recording()
            ├─→ Construye comando ffmpeg
            ├─→ Inicia proceso ffmpeg
            └─→ Callback: _on_screen_started()

... grabación en curso ...

Usuario presiona "Stop" o ACC se cierra
    ↓
MainWindow.stop_recording()
    ├─→ ScreenRecorder.stop_recording()
    │       ├─→ Finaliza proceso ffmpeg
    │       └─→ Callback: _on_screen_stopped()
    │
    └─→ TelemetryRecorder.stop_recording()
            ├─→ Guarda telemetry.json
            └─→ Callback: _on_telemetry_stopped()
```

## Próximas Mejoras Sugeridas

1. **Integración con ACC Shared Memory**
   - Conectar `TelemetryRecorder` con la memoria compartida de ACC
   - Leer datos reales de telemetría en el `_recording_loop()`

2. **Sistema de Plugins**
   - Permitir añadir procesadores de telemetría personalizados
   - Exportadores adicionales (Excel, bases de datos)

3. **Configuración Persistente**
   - Guardar configuración de grabadores en archivo
   - Perfiles de grabación predefinidos

4. **Compresión de Video Asíncrona**
   - Post-procesar videos grabados para reducir tamaño
   - Queue de procesamiento en background

5. **Tests Unitarios**
   - Crear tests para `TelemetryRecorder`
   - Crear tests para `ScreenRecorder`
   - Mock de procesos ffmpeg

## Conclusión

La refactorización ha logrado:
- ✅ Código más limpio y organizado
- ✅ Mejor arquitectura del software
- ✅ Mayor facilidad de mantenimiento
- ✅ Preparación para futuras funcionalidades
- ✅ Separación clara entre UI y lógica de negocio

Los módulos `core` ahora contienen toda la lógica de negocio de la aplicación, mientras que `gui` se enfoca únicamente en la presentación y la interacción con el usuario.
