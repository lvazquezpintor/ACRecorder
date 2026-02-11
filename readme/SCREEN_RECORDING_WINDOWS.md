# 🪟 Guía: Grabación de Pantalla en Windows

## Requisitos

### 1. Instalar ffmpeg

Hay varias formas de instalar ffmpeg en Windows:

#### Opción 1: Chocolatey (Recomendado)
```powershell
# Abre PowerShell como Administrador
choco install ffmpeg
```

#### Opción 2: Scoop
```powershell
# Abre PowerShell
scoop install ffmpeg
```

#### Opción 3: Instalación Manual
1. Descarga ffmpeg desde: https://www.gyan.dev/ffmpeg/builds/
2. Descarga la versión "ffmpeg-release-essentials.zip"
3. Extrae el archivo ZIP a una ubicación (ej: `C:\ffmpeg`)
4. Añadir al PATH:
   - Busca "Variables de entorno" en el menú Inicio
   - Click en "Variables de entorno"
   - En "Variables del sistema", selecciona "Path" y click "Editar"
   - Click "Nuevo" y añade la ruta al folder `bin` (ej: `C:\ffmpeg\bin`)
   - Click "Aceptar" en todas las ventanas
5. **Reinicia la terminal/aplicación**

#### Verificar instalación
```cmd
ffmpeg -version
```

## Características de Windows

### Captura de Pantalla: gdigrab

Windows usa `gdigrab` (GDI Graphics Grabber) para capturar la pantalla:

- ✅ Captura toda la pantalla principal automáticamente
- ✅ Captura el cursor del mouse
- ✅ No requiere permisos especiales
- ✅ Alto rendimiento
- ⚠️ Solo captura la pantalla principal (monitor 1)

### Captura de Audio: dshow

Para capturar audio en Windows se usa DirectShow (`dshow`):

- ⚠️ Requiere configuración adicional
- 🔊 Necesitas habilitar "Mezcla estéreo" (Stereo Mix)
- 🎤 O puedes capturar solo el micrófono
- 💡 Recomendado: Grabar sin audio (`audio=False`) para mayor confiabilidad

## Configuración de Audio del Sistema

### Habilitar "Mezcla estéreo" (Stereo Mix)

Si quieres capturar el audio del sistema:

1. **Click derecho** en el icono de volumen (barra de tareas)
2. Selecciona **"Sonidos"** o **"Configuración de sonido"**
3. Ve a la pestaña **"Grabación"**
4. **Click derecho** en el área vacía → **"Mostrar dispositivos deshabilitados"**
5. Busca **"Mezcla estéreo"** o **"Stereo Mix"**
6. **Click derecho** → **"Habilitar"**
7. **Click derecho** → **"Establecer como dispositivo predeterminado"**

**Nota**: No todas las tarjetas de sonido tienen Stereo Mix disponible.

## Script de Diagnóstico

Ejecuta el script de diagnóstico para verificar tu configuración:

```cmd
python diagnostico_screen_windows.py
```

El script:
1. ✅ Verifica que ffmpeg esté instalado
2. 📹 Muestra información sobre gdigrab
3. 🔊 Lista dispositivos de audio disponibles
4. 🎬 Hace una prueba de grabación de 3 segundos
5. 🔊 Prueba grabación con audio (opcional)
6. 📋 Genera un resumen con recomendaciones

## Ejemplos de Uso

### Ejemplo Básico (Sin Audio - Recomendado)

```python
from pathlib import Path
from core import ScreenRecorder
import time

output_dir = Path("./grabaciones")
recorder = ScreenRecorder(output_dir)

# Configurar sin audio (más confiable)
recorder.configure(
    fps=30,
    preset='ultrafast',
    audio=False,  # Sin audio
    capture_cursor=True
)

# Configurar callbacks para ver progreso
recorder.on_recording_started = lambda path: print(f"📹 Grabando: {path}")
recorder.on_recording_stopped = lambda dur: print(f"✅ Completado: {dur:.1f}s")
recorder.on_error = lambda msg: print(f"❌ Error: {msg}")

# Grabar
recorder.start_recording("mi_grabacion.mp4")
time.sleep(10)  # Grabar 10 segundos
recorder.stop_recording()
```

### Ejemplo con Audio (Requiere Stereo Mix)

```python
recorder.configure(
    fps=30,
    preset='ultrafast',
    audio=True,  # Intentar capturar audio
    audio_codec='aac',
    audio_bitrate='128k',
    capture_cursor=True
)

recorder.start_recording("grabacion_con_audio.mp4")
time.sleep(10)
recorder.stop_recording()
```

### Integración con main_window.py

El código ya está integrado en `main_window.py`:

```python
# En __init__
self.screen_recorder = ScreenRecorder(self.output_dir)

# Configurar para Windows
self.screen_recorder.configure(
    fps=30,
    preset='ultrafast',
    audio=False  # Cambiar a True si Stereo Mix está configurado
)

# Callbacks
self.screen_recorder.on_recording_started = self._on_screen_started
self.screen_recorder.on_recording_stopped = self._on_screen_stopped
self.screen_recorder.on_error = self._on_screen_error
```

## Configuración Recomendada

### Para Grabación de Juegos

```python
recorder.configure(
    fps=60,              # 60 fps para juegos fluidos
    preset='fast',       # Balance entre calidad y rendimiento
    crf=18,             # Alta calidad
    audio=False,        # Desactivar si no usas Stereo Mix
    capture_cursor=True
)
```

### Para Grabación de Tutoriales

```python
recorder.configure(
    fps=30,              # 30 fps es suficiente
    preset='medium',     # Mejor calidad
    crf=20,             # Balance calidad/tamaño
    audio=True,         # Si tienes Stereo Mix configurado
    capture_cursor=True
)
```

### Para Grabación Rápida/Pruebas

```python
recorder.configure(
    fps=24,              # 24 fps mínimo
    preset='ultrafast',  # Máximo rendimiento
    crf=28,             # Menor tamaño de archivo
    audio=False,
    capture_cursor=True
)
```

## Solución de Problemas

### ❌ Error: "ffmpeg no está instalado"

**Solución**:
1. Verifica que ffmpeg esté en el PATH: `ffmpeg -version`
2. Reinstala ffmpeg siguiendo las instrucciones arriba
3. **Reinicia la terminal/aplicación** después de instalar

### ❌ Video se crea pero está vacío o corrupto

**Causas posibles**:
- Antivirus bloqueando ffmpeg
- Permisos insuficientes
- Codec no soportado

**Soluciones**:
1. Ejecuta la aplicación como Administrador
2. Añade ffmpeg a las excepciones del antivirus
3. Usa `preset='ultrafast'` y `crf=23`

### ❌ Error: "Cannot find device 'Mezcla estéreo'"

**Causa**: Audio del sistema no configurado

**Soluciones**:
1. Habilita Stereo Mix (ver instrucciones arriba)
2. **O** usa `audio=False` para grabar sin audio
3. **O** captura solo micrófono cambiando el nombre del dispositivo

### ❌ Video se reproduce mal o con lag

**Causa**: Configuración demasiado exigente para el hardware

**Soluciones**:
1. Reduce FPS: `fps=24` o `fps=30`
2. Usa preset más rápido: `preset='ultrafast'`
3. Reduce resolución: `resolution=(1280, 720)`
4. Aumenta CRF: `crf=28` (menor calidad, menor tamaño)

### ⚠️ El cursor no se captura

**Solución**:
```python
recorder.configure(capture_cursor=True)
```

### ⚠️ Solo captura monitor principal

**Limitación de gdigrab**: Solo captura el monitor 1

**Alternativas**:
- Mueve la aplicación al monitor principal antes de grabar
- Usa software adicional como OBS Studio para captura multi-monitor

## Comparación con otras Plataformas

| Característica | Windows (gdigrab) | macOS (avfoundation) | Linux (x11grab) |
|----------------|-------------------|----------------------|-----------------|
| Permisos especiales | ❌ No | ✅ Sí | ❌ No |
| Captura cursor | ✅ Sí | ✅ Sí | ✅ Sí |
| Captura audio sistema | ⚠️ Con configuración | ✅ Directo | ⚠️ Con PulseAudio |
| Multi-monitor | ❌ Solo principal | ✅ Cualquiera | ✅ Cualquiera |
| Rendimiento | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Presets de ffmpeg

| Preset | Velocidad | Calidad | Tamaño | Uso Recomendado |
|--------|-----------|---------|--------|-----------------|
| ultrafast | ⚡⚡⚡⚡⚡ | ⭐ | 💾💾💾💾 | Grabación en tiempo real |
| veryfast | ⚡⚡⚡⚡ | ⭐⭐ | 💾💾💾 | Grabación de juegos |
| fast | ⚡⚡⚡ | ⭐⭐⭐ | 💾💾 | Balance |
| medium | ⚡⚡ | ⭐⭐⭐⭐ | 💾 | Post-producción |
| slow | ⚡ | ⭐⭐⭐⭐⭐ | 💾 | Máxima calidad |

## Valores de CRF

| CRF | Calidad | Tamaño | Uso |
|-----|---------|--------|-----|
| 18 | Excelente | Grande | Producción profesional |
| 20 | Muy buena | Medio-Grande | Tutoriales, presentaciones |
| 23 | Buena (default) | Medio | Uso general |
| 28 | Aceptable | Pequeño | Pruebas, borradores |

## Checklist Pre-Grabación

- [ ] ffmpeg instalado y en PATH
- [ ] Script de diagnóstico ejecutado sin errores
- [ ] Configuración ajustada a tus necesidades
- [ ] Disco con espacio suficiente
- [ ] Si necesitas audio: Stereo Mix habilitado
- [ ] Callbacks configurados para monitoreo

## Recursos Adicionales

- **ffmpeg Windows builds**: https://www.gyan.dev/ffmpeg/builds/
- **Chocolatey**: https://chocolatey.org/
- **VB-Audio Virtual Cable**: https://vb-audio.com/Cable/
- **Documentación ffmpeg**: https://ffmpeg.org/documentation.html

## Archivos Relacionados

- 📝 `core/screen_recorder.py` - Implementación
- 🔍 `diagnostico_screen_windows.py` - Script de diagnóstico
- 📖 `SCREEN_RECORDING_MACOS.md` - Guía para macOS
- 💻 `ejemplos_uso_grabadores.py` - Ejemplos de código

---

**Última actualización**: 2025-02-11  
**Probado en**: Windows 10, Windows 11  
**ffmpeg versión recomendada**: 6.0 o superior
