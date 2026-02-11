# 🍎 Solución: Grabación de Pantalla en macOS

## Problema Identificado

La grabación de pantalla en macOS tiene requisitos y configuraciones especiales que no estaban implementadas correctamente en la versión anterior del código.

## Cambios Implementados

### 1. Detección Automática de Dispositivos macOS

```python
def _get_macos_devices(self) -> Dict[str, List[str]]:
    """Obtiene la lista de dispositivos disponibles en macOS"""
    # Lista automáticamente dispositivos de video y audio
    # Cachea los resultados para no ejecutar múltiples veces
```

### 2. Selección Inteligente de Pantalla

```python
def _get_macos_screen_index(self) -> str:
    """Busca el dispositivo de captura de pantalla"""
    # Busca "Capture screen" en la lista de dispositivos
    # Retorna el índice correcto automáticamente
```

### 3. Configuración Mejorada para macOS

```python
# Nuevas opciones específicas para macOS
cmd.extend([
    '-capture_cursor', '1',          # Captura el cursor
    '-capture_mouse_clicks', '1',    # Captura clicks del mouse
    '-pix_fmt', 'yuv420p'           # Compatibilidad con reproductores
])
```

### 4. Manejo Mejorado de Errores

- Log del comando ejecutado para debugging
- Verificación inmediata de que ffmpeg inició correctamente
- Mensajes de error más descriptivos con stdout completo
- Mejor manejo de señales en macOS (SIGINT en lugar de 'q')

## Requisitos para macOS

### 1. Instalar ffmpeg

```bash
# Opción 1: Con Homebrew (recomendado)
brew install ffmpeg

# Opción 2: Con MacPorts
sudo port install ffmpeg

# Verificar instalación
ffmpeg -version
```

### 2. Permisos de Grabación de Pantalla

⚠️ **MUY IMPORTANTE**: macOS requiere permisos explícitos para grabar la pantalla.

#### Pasos para otorgar permisos:

1. Abre **Preferencias del Sistema** (System Settings)
2. Ve a **Privacidad y Seguridad** (Privacy & Security)
3. Selecciona **Grabación de Pantalla** (Screen Recording) en la lista izquierda
4. Asegúrate de que tu aplicación esté marcada:
   - **Python** (si ejecutas desde terminal)
   - **Terminal** (si usas Terminal)
   - **Visual Studio Code** (si ejecutas desde VS Code)
   - **PyCharm** (si ejecutas desde PyCharm)

#### Después de otorgar permisos:

- **IMPORTANTE**: Reinicia la aplicación/terminal
- En algunos casos, necesitas cerrar sesión y volver a entrar
- Si el problema persiste, reinicia el Mac

### 3. Verificar Dispositivos Disponibles

Usa el script de diagnóstico para ver los dispositivos:

```bash
python3 diagnostico_screen_macos.py
```

O manualmente con ffmpeg:

```bash
ffmpeg -f avfoundation -list_devices true -i ""
```

Salida esperada:
```
[AVFoundation indev @ ...] AVFoundation video devices:
[AVFoundation indev @ ...] [0] FaceTime HD Camera
[AVFoundation indev @ ...] [1] Capture screen 0
[AVFoundation indev @ ...] [2] Capture screen 1
[AVFoundation indev @ ...] AVFoundation audio devices:
[AVFoundation indev @ ...] [0] MacBook Pro Microphone
```

## Uso Actualizado

### Ejemplo Básico (Sin Audio)

```python
from pathlib import Path
from core import ScreenRecorder

output_dir = Path("./grabaciones")
recorder = ScreenRecorder(output_dir)

# Configurar sin audio (más confiable en macOS)
recorder.configure(
    fps=30,
    preset='ultrafast',
    audio=False,  # Desactivar audio
    capture_cursor=True
)

# Grabar
recorder.start_recording("test.mp4")
time.sleep(5)  # Grabar 5 segundos
recorder.stop_recording()
```

### Ejemplo con Audio

```python
recorder.configure(
    fps=30,
    preset='ultrafast',
    audio=True,  # Intentar capturar audio
    capture_cursor=True
)

recorder.start_recording("test_audio.mp4")
time.sleep(5)
recorder.stop_recording()
```

### Listar Dispositivos Disponibles

```python
# Solo funciona en macOS
devices = recorder.list_macos_devices()
print("Dispositivos de video:", devices['video'])
print("Dispositivos de audio:", devices['audio'])
```

## Script de Diagnóstico

Ejecuta el script de diagnóstico incluido para identificar problemas:

```bash
python3 diagnostico_screen_macos.py
```

El script:
1. ✅ Verifica que ffmpeg esté instalado
2. 📹 Lista todos los dispositivos disponibles
3. 🔒 Explica cómo configurar permisos
4. 🎬 Hace una prueba de grabación de 3 segundos
5. 🔊 Prueba grabación con audio
6. 📋 Genera un resumen con recomendaciones

## Solución de Problemas Comunes

### Error: "Input/output error"

**Causa**: No se otorgaron permisos de grabación de pantalla

**Solución**:
1. Ve a Preferencias del Sistema → Privacidad → Grabación de Pantalla
2. Marca la aplicación/terminal
3. **Reinicia la aplicación completamente**

### Error: "Device not found" o "No such device"

**Causa**: Índice de dispositivo incorrecto

**Solución**:
1. Ejecuta `diagnostico_screen_macos.py` para ver los dispositivos
2. El índice correcto suele ser `1` o el que dice "Capture screen"
3. El código ahora lo detecta automáticamente

### Video se crea pero está vacío (0 KB o muy pequeño)

**Causa**: ffmpeg se cerró inmediatamente por falta de permisos

**Solución**:
1. Revisa los logs de error en la callback `on_error`
2. Verifica permisos de grabación de pantalla
3. Ejecuta el script de diagnóstico

### Audio no se captura

**Causa**: Dispositivo de audio no disponible o permisos de micrófono

**Solución**:
1. Usa `audio=False` para grabar solo video
2. Otorga permisos de micrófono en Preferencias del Sistema
3. Verifica que hay dispositivos de audio: `recorder.list_macos_devices()`

### Video no se puede reproducir en QuickTime

**Causa**: Formato de píxel incompatible

**Solución**: Ya está corregido con `pixel_format='yuv420p'` por defecto

## Configuración Recomendada para macOS

```python
recorder.configure(
    fps=30,              # 30 fps es suficiente para la mayoría de casos
    preset='ultrafast',  # Mejor rendimiento en tiempo real
    crf=23,             # Balance entre calidad y tamaño (18=mejor, 28=menor)
    audio=False,        # Desactivar si no es necesario
    capture_cursor=True, # Capturar cursor del mouse
    pixel_format='yuv420p'  # Compatibilidad con reproductores
)
```

## Comparación: Antes vs Después

### Antes (Código Antiguo)
```python
# ❌ Usaba índice fijo '1:0' sin verificar
cmd.extend(['-i', '1:0'])
# ❌ No detectaba dispositivos
# ❌ No verificaba errores inmediatos
# ❌ Formato de píxel no especificado
```

### Después (Código Nuevo)
```python
# ✅ Detecta automáticamente el índice correcto
screen_index = self._get_macos_screen_index()
# ✅ Lista y cachea dispositivos
devices = self._get_macos_devices()
# ✅ Verifica que ffmpeg inició correctamente
if self.ffmpeg_process.poll() is not None:
    # Error inmediato
# ✅ Formato de píxel compatible
cmd.extend(['-pix_fmt', 'yuv420p'])
```

## Checklist de Verificación

Antes de reportar un problema, verifica:

- [ ] ffmpeg está instalado (`ffmpeg -version`)
- [ ] Permisos de grabación de pantalla otorgados
- [ ] Aplicación/terminal reiniciada después de otorgar permisos
- [ ] Script de diagnóstico ejecutado sin errores
- [ ] Dispositivos listados correctamente
- [ ] Prueba básica de grabación funciona

## Próximos Pasos

Si después de seguir todos estos pasos sigue sin funcionar:

1. Ejecuta el script de diagnóstico y guarda la salida completa
2. Verifica la versión de macOS (`sw_vers`)
3. Verifica la versión de ffmpeg (`ffmpeg -version`)
4. Comparte los logs de error completos

## Archivos Actualizados

- ✏️ `core/screen_recorder.py` - Soporte mejorado para macOS
- ✨ `diagnostico_screen_macos.py` - Script de diagnóstico nuevo
- 📝 `SCREEN_RECORDING_MACOS.md` - Esta documentación

---

**Última actualización**: 2025-02-11  
**Probado en**: macOS Sonoma 14.x, macOS Sequoia 15.x  
**ffmpeg versión recomendada**: 6.0 o superior
