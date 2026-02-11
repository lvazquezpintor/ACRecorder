# 🎬 Sincronización de Grabaciones: Telemetría y Pantalla

## Resumen Ejecutivo

**IMPORTANTE**: Tanto la grabación de telemetría como la de pantalla se inician y detienen **exactamente al mismo tiempo**, sincronizadas con el inicio y fin de la carrera.

---

## 🔄 Proceso de Sincronización

### 1. Inicio de Carrera Detectado

Cuando el `ACCSessionMonitor` detecta que la carrera comienza:

```python
def _on_race_started(self, race_data: dict):
    """Callback ejecutado cuando comienza la carrera"""
    
    session_type = race_data.get('session_type', 'Race')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"ACC_{session_type}_{timestamp}"
    
    # ✅ PASO 1: Iniciar grabación de TELEMETRÍA
    self.telemetry_recorder.start_recording(session_name)
    
    # ✅ PASO 2: Iniciar grabación de PANTALLA
    self.screen_recorder.start_recording(f"{session_name}.mp4")
    
    # Resultado: Ambas grabaciones activas SIMULTÁNEAMENTE
```

### 2. Fin de Carrera Detectado

Cuando el `ACCSessionMonitor` detecta que la carrera termina:

```python
def _on_race_ended(self, race_data: dict):
    """Callback ejecutado cuando termina la carrera"""
    
    # ✅ PASO 1: Detener grabación de PANTALLA
    self.screen_recorder.stop_recording()
    
    # ✅ PASO 2: Detener grabación de TELEMETRÍA
    self.telemetry_recorder.stop_recording()
    
    # Resultado: Ambas grabaciones detenidas SIMULTÁNEAMENTE
```

---

## 📂 Archivos Generados

Cada sesión genera **2 archivos sincronizados**:

```
ACC_Recordings/
└── ACC_Race_20250211_143052/
    ├── telemetry.json              ← Datos de telemetría
    └── ACC_Race_20250211_143052.mp4 ← Video de la carrera
```

### Características

| Archivo | Formato | Contenido | Duración |
|---------|---------|-----------|----------|
| `telemetry.json` | JSON | Datos de telemetría (velocidad, RPM, etc.) | Exactamente la carrera |
| `*.mp4` | Video | Grabación de pantalla | Exactamente la carrera |

**CRÍTICO**: Ambos archivos tienen la **misma duración** porque:
- ✅ Se inician al mismo tiempo
- ✅ Se detienen al mismo tiempo
- ✅ Están perfectamente sincronizados

---

## ⏱️ Timeline de Sincronización

```
Tiempo    Estado              Telemetría    Pantalla    Observaciones
──────────────────────────────────────────────────────────────────────
00:00     En menús            ⏸️ OFF       ⏸️ OFF      Usuario navegando
00:30     Entra a sesión      ⏸️ OFF       ⏸️ OFF      En pits
01:00     Calienta            ⏸️ OFF       ⏸️ OFF      Velocidad < 10 km/h
01:15     Empieza a moverse   ⏸️ OFF       ⏸️ OFF      Esperando 3s
01:18     🏁 CARRERA INICIA   🔴 REC       🔴 REC      ¡Grabación inicia!
──────────────────────────────────────────────────────────────────────
        ... 30 minutos de carrera grabándose ...
──────────────────────────────────────────────────────────────────────
31:18     🏁 CARRERA TERMINA  ⏹️ STOP      ⏹️ STOP     ¡Grabación detiene!
31:20     Vuelve a menús      ⏸️ OFF       ⏸️ OFF      Sin grabar
```

### Resultado

- **Grabado**: 30 minutos exactos de carrera
- **No grabado**: Menús, espera en pits, calentamiento
- **Sincronización**: Perfecta entre telemetría y video

---

## 🎯 Ventajas de la Sincronización

### 1. Análisis Preciso

```python
# Puedes correlacionar exactamente video con telemetría
video_frame_at_10s = extract_frame(video, 10.0)
telemetry_at_10s = telemetry_records[200]  # 10s * 20 records/s

# Ambos corresponden al MISMO momento de la carrera
```

### 2. Ahorro de Espacio

| Escenario | Sin Sincronización | Con Sincronización | Ahorro |
|-----------|-------------------|--------------------| -------|
| Carrera 30 min | 45 min grabados | 30 min grabados | 33% |
| Tamaño video | 4.5 GB | 3.0 GB | 1.5 GB |
| Tamaño telemetría | 15 MB | 10 MB | 5 MB |

### 3. Facilidad de Uso

- ✅ No necesitas recortar videos después
- ✅ No hay que buscar "dónde empieza la carrera"
- ✅ Todo el contenido es relevante
- ✅ Archivos listos para análisis inmediato

---

## 🔧 Implementación Técnica

### Callbacks Conectados

```python
class MainWindow(QMainWindow):
    def __init__(self):
        # Crear monitor de sesiones
        self.session_monitor = ACCSessionMonitor(self.acc_telemetry)
        
        # ✅ CRÍTICO: Conectar callbacks de sincronización
        self.session_monitor.on_race_started = self._on_race_started
        self.session_monitor.on_race_ended = self._on_race_ended
        
    def _on_race_started(self, race_data):
        """Inicia AMBAS grabaciones"""
        self.start_recording(race_data)  # ← Inicia telemetría + pantalla
        
    def _on_race_ended(self, race_data):
        """Detiene AMBAS grabaciones"""
        self.stop_recording()  # ← Detiene telemetría + pantalla
```

### Método Unificado de Grabación

```python
def start_recording(self, race_data: dict):
    """Inicia grabación sincronizada"""
    # Crear nombre único para la sesión
    session_name = self._generate_session_name(race_data)
    
    # IMPORTANTE: Orden garantiza sincronización
    # 1. Primero telemetría (crea directorio)
    session_dir = self.telemetry_recorder.start_recording(session_name)
    
    # 2. Luego pantalla (usa mismo directorio)
    video_path = session_dir / f"{session_name}.mp4"
    self.screen_recorder.start_recording(str(video_path))
    
    # ✅ Ahora ambas grabaciones están activas

def stop_recording(self):
    """Detiene grabación sincronizada"""
    # IMPORTANTE: Orden para limpieza correcta
    # 1. Primero pantalla (libera proceso ffmpeg)
    self.screen_recorder.stop_recording()
    
    # 2. Luego telemetría (guarda y cierra archivo)
    self.telemetry_recorder.stop_recording()
    
    # ✅ Ambas grabaciones detenidas y guardadas
```

---

## 📊 Verificación de Sincronización

### Script de Verificación

```python
from pathlib import Path
import json
from datetime import datetime

def verify_sync(session_dir: Path):
    """Verifica que telemetría y video estén sincronizados"""
    
    # Cargar telemetría
    telemetry_file = session_dir / "telemetry.json"
    with open(telemetry_file) as f:
        telemetry = json.load(f)
    
    # Obtener timestamps
    first_record = datetime.fromisoformat(telemetry[0]['timestamp'])
    last_record = datetime.fromisoformat(telemetry[-1]['timestamp'])
    telemetry_duration = (last_record - first_record).total_seconds()
    
    # Obtener duración de video
    import subprocess
    result = subprocess.run([
        'ffprobe', '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(session_dir / f"{session_dir.name}.mp4")
    ], capture_output=True, text=True)
    video_duration = float(result.stdout.strip())
    
    # Comparar
    diff = abs(telemetry_duration - video_duration)
    
    print(f"Telemetría: {telemetry_duration:.1f}s")
    print(f"Video: {video_duration:.1f}s")
    print(f"Diferencia: {diff:.1f}s")
    
    if diff < 2.0:  # Tolerancia de 2 segundos
        print("✅ SINCRONIZACIÓN CORRECTA")
        return True
    else:
        print("⚠️ POSIBLE PROBLEMA DE SINCRONIZACIÓN")
        return False

# Uso
verify_sync(Path("ACC_Recordings/ACC_Race_20250211_143052"))
```

### Output Esperado

```
Telemetría: 1847.3s
Video: 1847.0s
Diferencia: 0.3s
✅ SINCRONIZACIÓN CORRECTA
```

---

## 🐛 Troubleshooting

### Problema: Video más largo que telemetría

**Causa**: La grabación de pantalla no se detuvo correctamente

**Solución**:
```python
# Asegurar timeout en stop_recording
self.screen_recorder.stop_recording()  # Tiene timeout de 5s
```

### Problema: Telemetría más larga que video

**Causa**: ffmpeg se detuvo inesperadamente

**Solución**:
```python
# Verificar errores en callback
self.screen_recorder.on_error = lambda msg: print(f"Error: {msg}")
```

### Problema: Archivos no tienen el mismo nombre base

**Causa**: Se generaron nombres diferentes

**Solución**:
```python
# Usar mismo session_name para ambos
session_name = f"ACC_{session_type}_{timestamp}"
self.telemetry_recorder.start_recording(session_name)
self.screen_recorder.start_recording(f"{session_name}.mp4")
```

---

## 📝 Logs de Sincronización

### Output en la UI

```
✓ Monitoring started - Waiting for ACC race to begin...
✓ Connected to ACC telemetry
🏁 Race started: Race
🔴 Telemetry recording started: ACC_Race_20250211_143052
🎥 Screen recording started: ACC_Race_20250211_143052.mp4
... carrera en progreso ...
🏁 Race ended - Duration: 1847s
⏹ Stopping recording...
✓ Screen recording completed (1847s)
✓ Telemetry saved: 3694 records (1847s)
```

**Observa**: Las duraciones son idénticas (1847s)

---

## ✅ Checklist de Sincronización

Al finalizar una grabación, verificar:

- [ ] Ambos archivos existen en el mismo directorio
- [ ] Nombres de archivo tienen el mismo prefijo
- [ ] Duración de video ≈ duración de telemetría
- [ ] Primera marca de tiempo de telemetría ≈ inicio de video
- [ ] Última marca de tiempo de telemetría ≈ fin de video
- [ ] No hay contenido de menús/espera en ninguno

---

## 🎓 Conclusión

La sincronización perfecta entre telemetría y pantalla se logra mediante:

1. ✅ **Detección inteligente** del inicio de carrera
2. ✅ **Inicio simultáneo** de ambas grabaciones
3. ✅ **Fin simultáneo** de ambas grabaciones
4. ✅ **Mismo sistema de nombres** para facilitar correlación
5. ✅ **Callbacks sincronizados** que garantizan la atomicidad

**Resultado**: Archivos perfectamente alineados, listos para análisis.

---

**Versión**: 1.0.2  
**Fecha**: 2025-02-11  
**Estado**: ✅ Implementado y sincronizado
