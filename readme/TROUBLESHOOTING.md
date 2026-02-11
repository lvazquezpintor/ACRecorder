# Guía de Solución de Problemas - ACC Race Recorder

## Problemas Comunes y Soluciones

### 1. FFmpeg no encontrado

#### Síntoma
```
❌ ERROR: FFmpeg no encontrado. Instala FFmpeg y añádelo al PATH
```

#### Soluciones

**A. Verificar instalación**
```bash
ffmpeg -version
```

Si no funciona, FFmpeg no está instalado o no está en el PATH.

**B. Instalar con Chocolatey (Recomendado)**
1. Instala Chocolatey desde: https://chocolatey.org/install
2. Abre PowerShell como Administrador
3. Ejecuta:
```powershell
choco install ffmpeg
```

**C. Instalación Manual**
1. Descarga FFmpeg: https://www.gyan.dev/ffmpeg/builds/
   - Descarga "ffmpeg-release-full.7z"
2. Extrae en `C:\ffmpeg`
3. Añade al PATH:
   - Presiona Win + R, escribe `sysdm.cpl`, Enter
   - Pestaña "Opciones avanzadas"
   - "Variables de entorno"
   - En "Variables del sistema", selecciona "Path" → "Editar"
   - "Nuevo" → Añade `C:\ffmpeg\bin`
   - OK en todo
4. **IMPORTANTE**: Cierra y reabre todas las terminales

**D. Verificar PATH**
```bash
echo %PATH%
```
Debe incluir la ruta de FFmpeg.

---

### 2. No se detecta ACC

#### Síntoma
```
Servicio activo - Esperando ACC...
```
Pero ACC está corriendo y no se inicia la grabación.

#### Soluciones

**A. Verificar Shared Memory en ACC**
1. En ACC, ve a: `Options → General → Shared Memory`
2. Asegúrate que esté **HABILITADA**
3. Reinicia ACC

**B. Ejecutar como Administrador**
1. Click derecho en `run_recorder.bat`
2. "Ejecutar como administrador"

**C. Verificar nombre del proceso**
Edita `config.py` y añade nombres alternativos:
```python
ACC_PROCESS_NAMES = [
    'AC2-Win64-Shipping.exe',
    'AC2.exe',
    'AssettoCorsa2.exe',
    'ACC.exe'  # Añadir si es necesario
]
```

**D. Verificar manualmente el proceso**
1. Abre Task Manager (Ctrl + Shift + Esc)
2. Busca procesos de ACC
3. Anota el nombre exacto
4. Añádelo a `ACC_PROCESS_NAMES` en `config.py`

---

### 3. Grabación con lag o stuttering

#### Síntoma
El juego se ralentiza o el video tiene saltos durante la grabación.

#### Soluciones

**A. Reducir calidad de grabación**
Edita `config.py`:
```python
'video': {
    'framerate': 24,  # Reducir de 30 a 24
    'preset': 'ultrafast',  # Ya en el más rápido
    'crf': 28  # Aumentar (menor calidad, menor carga)
}
```

**B. Usar grabación por hardware (NVENC/AMD)**
Edita el comando FFmpeg en `acc_recorder.py`:
```python
# Para NVIDIA
ffmpeg_cmd = [
    'ffmpeg',
    '-f', 'gdigrab',
    '-framerate', '30',
    '-i', 'desktop',
    '-c:v', 'h264_nvenc',  # Cambiar a NVENC
    '-preset', 'fast',
    '-crf', '23',
    str(video_file)
]

# Para AMD
# Cambiar '-c:v', 'h264_amf'
```

**C. Cerrar otras aplicaciones**
- Cierra navegadores, Discord, OBS, etc.
- Desactiva overlays (Steam, Discord, etc.)

**D. Grabar en SSD**
Cambia el directorio de salida a un SSD en `config.py`.

---

### 4. No se captura telemetría

#### Síntoma
```
✓ Grabación completada
✓ Telemetría guardada: 0 registros
```

#### Soluciones

**A. Verificar Shared Memory**
Como en problema #2, debe estar habilitada.

**B. Iniciar grabación en sesión activa**
- No funciona en menús
- Debe estar en Practice/Qualifying/Race activa
- Espera a estar en pista

**C. Verificar permisos**
1. Ejecuta como Administrador
2. Desactiva antivirus temporalmente (puede bloquear acceso a memoria)

**D. Test manual de Shared Memory**
Crea `test_telemetry.py`:
```python
from acc_telemetry import ACCTelemetry

acc = ACCTelemetry()
if acc.connect():
    print("✓ Conectado a ACC")
    data = acc.get_player_telemetry()
    print(f"Datos: {data}")
else:
    print("✗ No se pudo conectar")
```

Ejecuta mientras ACC está corriendo:
```bash
python test_telemetry.py
```

---

### 5. Python no encontrado

#### Síntoma
```
'python' no se reconoce como un comando interno o externo...
```

#### Soluciones

**A. Instalar Python**
1. Descarga desde: https://www.python.org/downloads/
2. **IMPORTANTE**: Durante instalación, marca "Add Python to PATH"
3. Instala

**B. Usar Python Launcher**
Si instalaste sin PATH, usa:
```bash
py -3 acc_recorder.py
```

**C. Añadir Python al PATH manualmente**
1. Busca donde instalaste Python (ej: `C:\Python39`)
2. Añade al PATH (como con FFmpeg):
   - `C:\Python39`
   - `C:\Python39\Scripts`

---

### 6. Archivo de video corrupto o vacío

#### Síntoma
El archivo `.mp4` no se reproduce o está vacío.

#### Soluciones

**A. Dejar que FFmpeg termine**
No cierres la aplicación abruptamente. Usa "Detener Servicio".

**B. Tiempo mínimo de grabación**
FFmpeg necesita unos segundos para inicializar. Si la sesión es muy corta (<5s), el video puede fallar.

**C. Verificar espacio en disco**
Asegúrate de tener suficiente espacio.

**D. Codec alternativo**
Prueba con otro codec en `config.py`:
```python
'codec': 'libx265'  # H.265 (más eficiente)
```

---

### 7. La aplicación se cierra inesperadamente

#### Síntoma
GUI se cierra sin mensaje de error.

#### Soluciones

**A. Ejecutar desde terminal**
```bash
venv\Scripts\activate
python acc_recorder.py
```
Verás el error completo.

**B. Verificar dependencias**
```bash
pip install -r requirements.txt --upgrade
```

**C. Log de errores**
Añade logging al código:
```python
import logging
logging.basicConfig(filename='acc_recorder.log', level=logging.DEBUG)
```

---

### 8. Telemetría con datos erróneos

#### Síntoma
Los valores de telemetría parecen incorrectos o son 0.

#### Soluciones

**A. Versión de ACC**
La estructura de Shared Memory puede cambiar entre versiones. Este código es compatible con versiones recientes (2023-2024).

**B. Actualizar offsets**
Si ACC se actualizó, los offsets de memoria pueden haber cambiado. Consulta:
- https://github.com/mdjarv/assettocorsacompetizione
- https://www.assettocorsa.net/forum/index.php?forums/acc-general-discussions.53/

**C. Usar Broadcasting SDK**
Para datos más confiables, implementa la Broadcasting API (ver README).

---

### 9. No aparecen standings/posiciones

#### Síntoma
`standings` está vacío o solo muestra el jugador.

#### Causa
Shared Memory básica de ACC no expone posiciones de otros coches.

#### Solución
Implementar Broadcasting SDK:

1. Instalar:
```bash
pip install accbroadcasting
```

2. Configurar ACC:
   - Archivo: `Documents\Assetto Corsa Competizione\Config\broadcasting.json`
   - Contenido:
```json
{
  "updListenerPort": 9000,
  "connectionPassword": "",
  "commandPassword": ""
}
```

3. Reiniciar ACC

4. Modificar `acc_telemetry.py` para usar Broadcasting (ver código comentado)

---

### 10. Errores de permisos al crear archivos

#### Síntoma
```
PermissionError: [Errno 13] Permission denied
```

#### Soluciones

**A. Ejecutar como Administrador**

**B. Cambiar directorio de salida**
En `config.py`:
```python
'base_directory': 'D:\\ACC_Recordings'  # Otra unidad
```

**C. Verificar antivirus**
Puede estar bloqueando escritura. Añade excepción para la carpeta.

---

## Diagnóstico General

### Crear script de diagnóstico
`diagnose.py`:
```python
import sys
import subprocess
import mmap

print("=== ACC Recorder Diagnostics ===\n")

# Python
print(f"Python: {sys.version}")

# FFmpeg
try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    print(f"FFmpeg: OK - {result.stdout.split()[2]}")
except:
    print("FFmpeg: NOT FOUND")

# Shared Memory test
try:
    test = mmap.mmap(-1, 1024, "Local\\acpmf_physics")
    print("ACC Shared Memory: ACCESSIBLE")
    test.close()
except:
    print("ACC Shared Memory: NOT ACCESSIBLE (ACC must be running)")

print("\n=== End Diagnostics ===")
```

Ejecutar:
```bash
python diagnose.py
```

---

## ¿Sigues teniendo problemas?

1. **Revisa el log** en la GUI de la aplicación
2. **Ejecuta desde terminal** para ver errores completos
3. **Crea un issue** en GitHub con:
   - Versión de Windows
   - Versión de Python
   - Versión de ACC
   - Log completo del error
   - Pasos para reproducir

---

## Logs Útiles

Añade al inicio de `acc_recorder.py`:
```python
import logging

logging.basicConfig(
    filename='acc_recorder.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

El archivo `acc_recorder.log` tendrá información detallada de lo que sucede.
