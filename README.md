# ACC Race Recorder 🏎️📹

Grabador automático de carreras para Assetto Corsa Competizione con telemetría sincronizada.

## Características

✅ **Grabación automática**: Detecta cuando inicias una carrera en ACC y comienza a grabar automáticamente  
✅ **Video en alta calidad**: Graba la pantalla completa a 30 FPS usando FFmpeg  
✅ **Telemetría sincronizada**: Captura datos cada segundo sincronizados con el video  
✅ **Interfaz GUI simple**: Control fácil con botones de inicio/detención y log de eventos  
✅ **Datos completos**: Posiciones, telemetría del coche, tiempos de vuelta y más  

## Datos Capturados

### Video
- Grabación de pantalla completa en MP4
- 30 FPS, codec H.264
- Calidad ajustable

### Telemetría JSON (cada segundo)
- **Información de sesión**: Tipo de sesión, tiempos de vuelta, estado
- **Posiciones**: Clasificación de pilotos (básica con Shared Memory, completa con Broadcasting SDK)
- **Telemetría del jugador**:
  - Acelerador, freno, volante
  - Velocidad, RPM, marcha
  - Combustible
  - Temperaturas y presiones de neumáticos
  - Velocidad vectorial

## Requisitos Previos

### 1. Python 3.8 o superior
Verifica tu versión:
```bash
python --version
```

### 2. FFmpeg
**IMPORTANTE**: FFmpeg debe estar instalado y en el PATH de Windows.

#### Instalación de FFmpeg:

**Opción A - Usando Chocolatey (Recomendado)**:
```bash
choco install ffmpeg
```

**Opción B - Descarga Manual**:
1. Descarga FFmpeg: https://ffmpeg.org/download.html#build-windows
2. Extrae el archivo ZIP
3. Añade la carpeta `bin` al PATH de Windows:
   - Busca "Variables de entorno" en Windows
   - Edita la variable "Path"
   - Añade la ruta a la carpeta `bin` de FFmpeg (ej: `C:\ffmpeg\bin`)

#### Verificar instalación de FFmpeg:
```bash
ffmpeg -version
```

### 3. Assetto Corsa Competizione
- El juego debe tener habilitada la **Shared Memory**
- Configuración en ACC: `Options → General → Shared Memory`

## Instalación

### 1. Clonar o descargar el proyecto
```bash
git clone https://github.com/tuusuario/acc-race-recorder.git
cd acc-race-recorder
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## Uso

### Inicio Rápido

1. **Iniciar la aplicación**:
```bash
python acc_recorder_gui.py
```
O simplemente ejecuta `run_recorder.bat`

2. **Interfaz con pestañas**:
   - **🎮 Control de Grabación**: Iniciar/detener el servicio y ver el log en tiempo real
   - **📁 Grabaciones**: Ver todas tus sesiones grabadas y reproducirlas
   - **📊 Visualizador**: Cargar y analizar telemetría con estadísticas detalladas
   - **⚙️ Configuración**: Ajustar calidad de video, FPS, intervalo de telemetría

3. **Iniciar el servicio**: 
   - Ve a la pestaña "Control de Grabación"
   - Click en "▶ Iniciar Servicio"

4. **Jugar ACC**: Inicia Assetto Corsa Competizione y comienza una sesión

5. **Grabación automática**: El servicio detectará la sesión y comenzará a grabar automáticamente

6. **Ver resultados**:
   - Ve a la pestaña "📁 Grabaciones"
   - Selecciona una sesión
   - Click en "▶ Reproducir Video" o "📊 Ver Telemetría"

7. **Finalizar**: Al terminar la carrera, la grabación se detendrá automáticamente

### Archivos de Salida

Las grabaciones se guardan en: `C:\Users\TuUsuario\ACC_Recordings\`

Estructura de carpetas:
```
ACC_Recordings/
├── ACC_20240208_153045/
│   ├── race_recording.mp4      # Video de la carrera
│   └── telemetry.json          # Datos de telemetría
├── ACC_20240208_164521/
│   ├── race_recording.mp4
│   └── telemetry.json
```

### Formato del JSON de Telemetría

```json
[
  {
    "second": 0,
    "timestamp": "2024-02-08T15:30:45.123456",
    "session": {
      "status": "Live",
      "session_type": "Race",
      "current_time_ms": 12500,
      "last_lap_time_ms": 92345,
      "best_lap_time_ms": 91234
    },
    "standings": [
      {
        "position": 1,
        "car_number": 0,
        "driver_name": "Player",
        "gap": "0.000",
        "laps": 5
      }
    ],
    "player_telemetry": {
      "gas": 0.850,
      "brake": 0.000,
      "fuel": 45.2,
      "gear": 4,
      "rpm": 7200,
      "steer_angle": -12.5,
      "speed_kmh": 185.3,
      "velocity": {
        "x": 45.2,
        "y": -0.5,
        "z": 12.3
      },
      "tyres": {
        "temperature": {
          "front_left": 85.5,
          "front_right": 86.2
        },
        "pressure": {
          "front_left": 27.8,
          "front_right": 27.9
        }
      }
    }
  }
]
```

## Configuración Avanzada

Edita `config.py` para personalizar:

```python
RECORDING_CONFIG = {
    'video': {
        'framerate': 60,  # Cambiar a 60 FPS
        'preset': 'medium',  # Mejor calidad (más lento)
        'crf': 18  # Mejor calidad visual
    },
    'telemetry': {
        'sample_rate': 0.5  # Capturar cada 0.5 segundos (más datos)
    }
}
```

## Troubleshooting

### "FFmpeg no encontrado"
- Verifica que FFmpeg esté en el PATH: `ffmpeg -version`
- Reinicia la terminal después de instalar FFmpeg
- Si instalaste manualmente, verifica la ruta en las variables de entorno

### "No se detecta ACC"
- Verifica que ACC esté corriendo
- Asegúrate de que Shared Memory esté habilitada en ACC
- El nombre del proceso puede variar según la versión

### "No se captura telemetría"
- ACC debe tener Shared Memory habilitada
- Ejecuta la aplicación como Administrador si hay problemas de permisos
- Verifica que estés en una sesión activa (no en menús)

### "Grabación con lag"
- Reduce el framerate a 24 o 30 FPS
- Cambia el preset de FFmpeg a 'ultrafast'
- Cierra otras aplicaciones que consuman recursos
- Considera grabar en resolución más baja

## Mejoras Futuras

### Implementar Broadcasting SDK (Standings Completos)
Para obtener posiciones detalladas de todos los pilotos:

1. Instalar SDK:
```bash
pip install accbroadcasting
```

2. Habilitar Broadcasting en ACC:
   - `Documents\Assetto Corsa Competizione\Config\broadcasting.json`
   - Configurar puerto y contraseña

3. Descomentar código de Broadcasting en `acc_telemetry.py`

### Otras Mejoras Posibles
- [ ] Selector de resolución de grabación
- [ ] Grabación solo de la ventana de ACC (no pantalla completa)
- [ ] Overlay con telemetría en el video
- [ ] Exportar a formatos alternativos (CSV para telemetría)
- [ ] Visualización de telemetría en gráficos
- [ ] Detección de incidentes/adelantamientos
- [ ] Múltiples perfiles de calidad de video

## Estructura del Proyecto

```
acc-race-recorder/
├── acc_recorder.py          # GUI principal y lógica del servicio
├── acc_telemetry.py         # Módulo de lectura de telemetría
├── config.py                # Configuración
├── requirements.txt         # Dependencias Python
└── README.md               # Este archivo
```

## Licencia

MIT License - Libre para uso personal y comercial

## Créditos

- FFmpeg: https://ffmpeg.org/
- ACC Shared Memory: https://www.assettocorsa.net/forum/

## Contribuciones

¡Pull requests son bienvenidos! Para cambios mayores, abre primero un issue para discutir los cambios propuestos.

---

**¿Problemas o preguntas?** Abre un issue en GitHub o contacta al desarrollador.

¡Disfruta grabando tus carreras! 🏁
