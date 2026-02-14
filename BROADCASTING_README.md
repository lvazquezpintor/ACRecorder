# ACC Broadcasting SDK - Guía de Uso

## ¿Qué es el Broadcasting SDK?

El Broadcasting SDK de ACC es un sistema UDP que permite obtener datos de **TODOS** los coches en una sesión, no solo el tuyo. Es la única forma oficial de obtener:

- ✅ Nombres de pilotos
- ✅ Posiciones en carrera
- ✅ Tiempos de vuelta de todos
- ✅ Gaps y deltas
- ✅ Información de equipos
- ✅ Números de coche

## Configuración Inicial

### 1. Habilitar Broadcasting en ACC

Edita el archivo:
```
Documents\Assetto Corsa Competizione\Config\broadcasting.json
```

Contenido:
```json
{
    "updListenerPort": 9000,
    "connectionPassword": "asd",
    "commandPassword": ""
}
```

**Importante**: 
- El archivo debe tener exactamente este formato
- Puedes cambiar el password si quieres
- El puerto por defecto es 9000

### 2. Reiniciar ACC

Después de editar `broadcasting.json`, reinicia ACC para que apliquen los cambios.

## Uso Básico

### Ejemplo Simple

```python
from core.broadcasting import ACCBroadcastingClient

# Crear cliente
broadcasting = ACCBroadcastingClient()

# Conectar
broadcasting.connect(
    display_name="MiApp",
    ip="127.0.0.1",
    port=9000,
    password="asd"
)

# Esperar que se reciban datos
import time
time.sleep(2)

# Obtener clasificación
standings = broadcasting.get_standings()

for entry in standings:
    print(f"{entry['position']}. {entry['driver_name']} - #{entry['car_number']}")

# Desconectar
broadcasting.disconnect()
```

### Integración con Shared Memory

```python
from core.acc_telemetry import ACCTelemetry
from core.broadcasting import ACCBroadcastingClient

# Conectar ambos
telemetry = ACCTelemetry()
broadcasting = ACCBroadcastingClient()

telemetry.connect()
broadcasting.connect(password="asd")

# Obtener datos combinados
player_data = telemetry.get_player_telemetry()  # TU coche
standings = broadcasting.get_standings()         # TODOS los coches

# Ahora tienes telemetría completa + posiciones
```

## Datos Disponibles

### get_standings()

Retorna lista de diccionarios con:

```python
{
    'position': 1,                    # Posición actual
    'car_index': 0,                   # Índice del coche
    'car_number': 23,                 # Número de carrera
    'driver_name': 'Juan Pérez',     # Nombre del piloto
    'team_name': 'Team Racing',       # Nombre del equipo
    'car_model': 2,                   # Modelo de coche (enum)
    'laps': 12,                       # Vueltas completadas
    'delta': 2345,                    # Delta en ms respecto al líder
    'best_session_lap': {...},        # Mejor vuelta de la sesión
    'last_lap': {...},                # Última vuelta
    'current_lap': {...},             # Vuelta actual
    'location': 1                     # Ubicación (Track/Pit)
}
```

### get_session_info()

Retorna información de la sesión:

```python
{
    'session_type': 3,        # Tipo (0=Practice, 3=Race, etc.)
    'phase': 5,               # Fase de la sesión
    'session_time': 1234.5,   # Tiempo de sesión
    'ambient_temp': 25,       # Temperatura ambiente °C
    'track_temp': 32,         # Temperatura pista °C
    'clouds': 0.3,            # Nubosidad (0-1)
    'rain_level': 0.0,        # Nivel de lluvia (0-1)
    'wetness': 0.2            # Humedad pista (0-1)
}
```

### get_track_data()

Retorna información del circuito:

```python
{
    'track_name': 'Monza',
    'track_id': 3,
    'track_meters': 5793,     # Longitud en metros
    'camera_sets': [...],      # Sets de cámaras disponibles
    'hud_pages': [...]         # Páginas HUD disponibles
}
```

## Callbacks (Opcional)

Puedes registrar callbacks para recibir datos automáticamente:

```python
def on_car_update(car_index, data):
    print(f"Coche {car_index} actualizado: Pos {data['position']}")

def on_entry_list(car_index, entry):
    print(f"Nuevo coche: {entry['drivers'][0]['first_name']}")

broadcasting.on_realtime_car_update = on_car_update
broadcasting.on_entry_list_update = on_entry_list

broadcasting.connect(password="asd")

# Los callbacks se llamarán automáticamente
```

## Frecuencia de Actualización

Por defecto: **250ms** (4 actualizaciones/segundo)

Puedes cambiarla al conectar:

```python
broadcasting.connect(
    password="asd",
    update_interval_ms=100  # 10 actualizaciones/segundo
)
```

**Rango válido**: 100ms - 1000ms

## Troubleshooting

### "Error conectando al Broadcasting"

1. Verifica que ACC esté corriendo
2. Verifica que `broadcasting.json` esté configurado
3. Reinicia ACC después de editar el archivo
4. Verifica que el password coincida
5. Verifica que el puerto 9000 esté libre

### "No recibo datos de clasificación"

1. Entra en una sesión (práctica, clasificación o carrera)
2. Espera 2-3 segundos después de conectar
3. Verifica que haya otros coches en la sesión
4. En sesiones offline, necesitas agregar AI

### "Los nombres aparecen como 'Unknown'"

Espera unos segundos. El Broadcasting primero envía los índices de coches y luego los detalles completos.

## Ejemplo Completo

Ver `example_broadcasting.py` para un ejemplo funcional completo.

## Integración con ACRecorder

Para integrar con tu sistema de grabación:

1. Conecta tanto Shared Memory como Broadcasting al inicio
2. En cada frame de grabación, captura:
   - Telemetría del jugador (Shared Memory)
   - Clasificación (Broadcasting)
3. Guarda ambos en tu formato de telemetría
4. Desconecta ambos al finalizar

```python
# En tu módulo de grabación
self.telemetry = ACCTelemetry()
self.broadcasting = ACCBroadcastingClient()

# Al iniciar grabación
self.telemetry.connect()
self.broadcasting.connect(password="asd")

# En cada frame
data = {
    'player': self.telemetry.get_player_telemetry(),
    'standings': self.broadcasting.get_standings(),
    'session': self.broadcasting.get_session_info()
}

# Al detener grabación
self.broadcasting.disconnect()
self.telemetry.disconnect()
```
