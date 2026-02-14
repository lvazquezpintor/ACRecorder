# ACC Recorder - Telemetría con Clasificación de Pilotos

Sistema completo de grabación de telemetría para Assetto Corsa Competizione que incluye:
- ✅ Telemetría completa de tu coche (Shared Memory)
- ✅ Posiciones y nombres de todos los pilotos (Broadcasting SDK)
- ✅ Exportación a JSON y CSV
- ✅ Análisis de sesiones grabadas

## 🚀 Inicio Rápido

### 1. Configurar Broadcasting en ACC

**IMPORTANTE**: Sin este paso, solo grabarás la telemetría de tu coche.

Edita el archivo:
```
Documents\Assetto Corsa Competizione\Config\broadcasting.json
```

Contenido (copia y pega):
```json
{
    "updListenerPort": 9000,
    "connectionPassword": "asd",
    "commandPassword": ""
}
```

**Reinicia ACC** después de editar el archivo.

### 2. Grabar una Sesión

```bash
python test_recording.py
```

1. Entra en ACC y ve a una sesión (práctica, clasificación o carrera)
2. El script se conectará automáticamente
3. Corre vueltas normalmente
4. Presiona `Ctrl+C` para detener la grabación

### 3. Analizar Grabaciones

```bash
python analyze_telemetry.py
```

Te mostrará todas las sesiones grabadas y podrás ver estadísticas detalladas.

## 📊 Datos Capturados

### De tu coche (Shared Memory)
- Velocidad, RPM, marcha
- Acelerador, freno, dirección
- Temperaturas de neumáticos (4 ruedas)
- Presiones de neumáticos (4 ruedas)
- Temperaturas de frenos (4 ruedas)
- Desgaste de neumáticos
- Fuerzas G (lateral, longitudinal, vertical)
- Deslizamiento de ruedas
- Control de tracción y ABS
- Combustible
- Y mucho más...

### De todos los pilotos (Broadcasting)
- ✅ Nombre del piloto
- ✅ Posición actual
- ✅ Número de coche
- ✅ Nombre del equipo
- ✅ Vueltas completadas
- ✅ Delta respecto al líder
- ✅ Mejor vuelta de la sesión
- ✅ Tiempo de última vuelta

### Información de Sesión
- Tipo de sesión (práctica, clasificación, carrera)
- Tiempo restante
- Condiciones climáticas (temperatura, lluvia, nubosidad)
- Información del circuito

## 📁 Estructura de Archivos Grabados

Cada sesión crea una carpeta con:

```
recordings/
└── ACC_20260215_143022/
    ├── session_info.json    # Info inicial de la sesión
    ├── telemetry.json       # Todos los datos capturados
    ├── summary.json         # Resumen de la grabación
    ├── telemetry.csv       # Telemetría en CSV (si se exporta)
    └── standings.csv       # Clasificación en CSV (si se exporta)
```

### Formato de telemetry.json

```json
[
  {
    "timestamp": "2026-02-15T14:30:22.123456",
    "player_telemetry": {
      "speed_kmh": 245.3,
      "rpm": 8500,
      "gear": 6,
      "gas": 1.0,
      "brake": 0.0,
      "tyres": {
        "temperature": {
          "front_left": 85.2,
          "front_right": 86.1,
          ...
        },
        "pressure": {
          "front_left": 27.5,
          ...
        }
      },
      ...
    },
    "standings": [
      {
        "position": 1,
        "driver_name": "Juan Pérez",
        "car_number": 23,
        "team_name": "Racing Team",
        "laps": 12,
        "delta": 0
      },
      {
        "position": 2,
        "driver_name": "María García",
        "car_number": 7,
        "laps": 12,
        "delta": 2345
      },
      ...
    ],
    "session_info": {...},
    "track_data": {...}
  },
  ...
]
```

## 🔧 Uso Programático

### Grabación Simple

```python
from pathlib import Path
from core.telemetry_recorder import TelemetryRecorder

# Crear grabador
recorder = TelemetryRecorder(
    output_dir=Path("recordings"),
    enable_broadcasting=True  # ¡Importante para posiciones!
)

# Iniciar grabación
recorder.start_recording()

# ... grabar durante un tiempo ...

# Detener y guardar
recorder.stop_recording()
recorder.disconnect_from_acc()
```

### Acceso Directo a Datos

```python
from core.acc_telemetry import ACCTelemetry
from core.broadcasting import ACCBroadcastingClient

# Shared Memory (tu coche)
telemetry = ACCTelemetry()
telemetry.connect()

player_data = telemetry.get_player_telemetry()
print(f"Velocidad: {player_data['speed_kmh']} km/h")

# Broadcasting (todos los coches)
broadcasting = ACCBroadcastingClient()
broadcasting.connect(password="asd")

standings = broadcasting.get_standings()
for entry in standings:
    print(f"{entry['position']}. {entry['driver_name']}")
```

### Configurar Broadcasting

```python
recorder = TelemetryRecorder(output_dir=Path("recordings"))

# Configurar antes de iniciar grabación
recorder.set_broadcasting_config(
    ip='127.0.0.1',
    port=9000,
    password='asd',
    update_interval_ms=250  # 4 actualizaciones/segundo
)

recorder.start_recording()
```

### Callbacks para Monitoreo

```python
def on_started(session_name):
    print(f"Grabación iniciada: {session_name}")

def on_update(data):
    standings = data.get('standings', [])
    print(f"Pilotos en pista: {len(standings)}")

def on_stopped(records, duration):
    print(f"Grabados {records} registros en {duration:.1f}s")

recorder.on_recording_started = on_started
recorder.on_telemetry_update = on_update
recorder.on_recording_stopped = on_stopped
```

## 📤 Exportación de Datos

### Exportar a CSV

```python
# Exportar telemetría completa
recorder.export_csv(
    filepath=Path("telemetry.csv"),
    flatten=True  # Aplana estructuras anidadas
)

# Exportar solo clasificación
recorder.export_standings_csv(
    filepath=Path("standings.csv")
)
```

### Cargar Sesión Grabada

```python
# Cargar telemetría
data = recorder.load_telemetry(Path("recordings/ACC_20260215_143022/telemetry.json"))

# Analizar datos
for record in data:
    player = record['player_telemetry']
    standings = record['standings']
    
    # Tu posición en ese momento
    session = record['session_info']
    your_position = session['position']
    
    print(f"Vuelta {session['completed_laps']}: Posición {your_position}")
```

## ⚙️ Configuración Avanzada

### Cambiar Frecuencia de Muestreo

```python
recorder = TelemetryRecorder(output_dir=Path("recordings"))
recorder.sample_rate = 20  # 20 samples/segundo (por defecto: 10)
```

### Deshabilitar Broadcasting

```python
# Solo grabar telemetría de tu coche
recorder = TelemetryRecorder(
    output_dir=Path("recordings"),
    enable_broadcasting=False  # Sin datos de otros pilotos
)
```

## 🐛 Solución de Problemas

### "No se pudo conectar al Broadcasting"

1. ✅ Verifica que `broadcasting.json` esté correctamente configurado
2. ✅ Reinicia ACC después de editar el archivo
3. ✅ Verifica que el password coincida (`"asd"` por defecto)
4. ✅ Asegúrate de estar en una sesión activa (no en menús)

### "No hay datos de clasificación"

1. ✅ Entra en una sesión con otros coches (online o con AI)
2. ✅ Espera 2-3 segundos después de conectar
3. ✅ Verifica que `enable_broadcasting=True`

### "Error al conectar a Shared Memory"

1. ✅ Asegúrate de que ACC esté corriendo
2. ✅ Entra en una sesión activa (driving)
3. ✅ El juego debe estar en modo ventana o sin bordes

## 📚 Archivos del Proyecto

```
ACRecorder/
├── core/
│   ├── broadcasting/
│   │   ├── __init__.py
│   │   ├── client.py          # Cliente UDP Broadcasting
│   │   └── protocol.py        # Enums y tipos de mensajes
│   ├── acc_telemetry.py       # Shared Memory client
│   └── telemetry_recorder.py  # Sistema de grabación
├── test_recording.py          # Script de grabación
├── analyze_telemetry.py       # Analizador de sesiones
├── example_broadcasting.py    # Ejemplos de uso
├── BROADCASTING_README.md     # Docs del Broadcasting
└── recordings/                # Sesiones grabadas (creado automáticamente)
```

## 🎯 Casos de Uso

### Análisis de Performance
Compara tus vueltas con las de otros pilotos viendo:
- Velocidades máximas por sector
- Diferencias de temperatura de neumáticos
- Puntos de frenada
- Uso de acelerador y freno

### Revisión de Carrera
Revive toda la carrera viendo:
- Cambios de posición
- Deltas con otros pilotos
- Estrategias de neumáticos
- Gestión de combustible

### Entrenamiento
Identifica áreas de mejora comparando:
- Tus mejores vueltas vs las del líder
- Consistencia en temperaturas
- Aprovechamiento del coche

## 📝 Notas

- Broadcasting solo funciona en PC (no consolas)
- Requiere ACC en modo ventana o sin bordes para Shared Memory
- Los datos de Broadcasting tienen ~250ms de delay
- Shared Memory se actualiza a 60Hz
- El sistema graba a 10Hz por defecto (configurable)

## 🤝 Contribuciones

Este proyecto está en desarrollo activo. Sugerencias y mejoras son bienvenidas!
