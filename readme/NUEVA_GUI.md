# ACC Race Recorder - GUI Integrada 🎮

## Nueva Aplicación Unificada

He creado `acc_recorder_gui.py` - una aplicación GUI completa que integra **TODO** en una sola interfaz con 4 pestañas:

---

## 🎮 Pestaña 1: Control de Grabación

**Funcionalidad principal:**
- ▶️ Botón "Iniciar Servicio" / ⏹ "Detener Servicio"
- Indicador visual de estado (círculo verde/rojo)
- **Información de sesión en tiempo real:**
  - ⏱️ Duración de la grabación actual
  - 📊 Número de registros de telemetría capturados
  - 📁 Nombre de la carpeta de la sesión
- **Log de eventos en tiempo real:**
  - Monitoreo de ACC
  - Inicio/fin de grabación
  - Errores y advertencias

**Cómo usar:**
1. Click en "▶ Iniciar Servicio"
2. El servicio queda monitoreando ACC en segundo plano
3. Cuando inicies una carrera en ACC, la grabación comienza automáticamente
4. Ves todo en tiempo real en el log

---

## 📁 Pestaña 2: Grabaciones

**Lista todas tus sesiones grabadas con:**
- 📅 Fecha y hora de la grabación
- ⏱️ Duración de la sesión
- 💾 Tamaño del archivo de video

**Acciones rápidas:**
- 🔄 **Actualizar Lista**: Refresca la lista de grabaciones
- 📂 **Abrir Carpeta**: Abre el directorio de grabaciones
- ▶️ **Reproducir Video**: Reproduce el MP4 seleccionado
- 📊 **Ver Telemetría**: Carga la telemetría en el visualizador
- 📁 **Abrir Carpeta** (sesión): Abre la carpeta de esa sesión específica

**Cómo usar:**
1. Haz doble click en una sesión para seleccionarla
2. Click en "▶ Reproducir Video" para ver la carrera
3. Click en "📊 Ver Telemetría" para analizar datos

---

## 📊 Pestaña 3: Visualizador de Telemetría

**Visualización integrada de datos:**
- 📂 **Cargar archivo JSON**: Selecciona un telemetry.json
- 🌐 **Abrir Visualizador Web**: Abre el HTML con gráficos interactivos

**Estadísticas automáticas mostradas:**
- 📊 Total de registros y duración
- 🏎️ Velocidad máxima y media
- 🔴 Total de bloqueos de rueda detectados
- ⚠️ Lista de momentos con bloqueos (segundos exactos)
- 💨 Fuerzas G máximas (lateral, frenada, aceleración)
- 🔥 Temperaturas de frenos (máxima y media)

**Cómo usar:**
1. Click en "📂 Cargar archivo JSON"
2. Selecciona un telemetry.json de tus grabaciones
3. Lee las estadísticas en pantalla
4. Click en "🌐 Abrir Visualizador Web" para gráficos detallados

---

## ⚙️ Pestaña 4: Configuración

**Ajusta la calidad de grabación:**

### Configuración de Video
- **FPS**: 24 / 30 / 60
  - 24 = Rendimiento óptimo
  - 30 = Equilibrio (recomendado)
  - 60 = Máxima fluidez (requiere más CPU)
  
- **Calidad (CRF)**: 18 / 23 / 28
  - 18 = Alta calidad (archivos grandes)
  - 23 = Calidad media (recomendado)
  - 28 = Baja calidad (archivos pequeños)
  
- **Preset**: ultrafast / fast / medium
  - ultrafast = Mínimo uso de CPU (recomendado durante juego)
  - fast = Equilibrio
  - medium = Mejor compresión (más CPU)

### Configuración de Telemetría
- **Intervalo**: 0.5 / 1 / 2 segundos
  - 0.5s = Datos muy detallados (archivos JSON grandes)
  - 1s = Balance (recomendado)
  - 2s = Datos menos frecuentes

### Directorio de Salida
- Cambia dónde se guardan las grabaciones
- Por defecto: `C:\Users\TuUsuario\ACC_Recordings`

**Cómo usar:**
1. Ajusta los valores según tu PC
2. Click en "💾 Guardar Configuración"

---

## 🚀 Ventajas de la GUI Integrada

### ✅ Todo en un Solo Lugar
- No necesitas múltiples ventanas o archivos
- Control, visualización y configuración unificados

### ✅ Fácil Acceso a Grabaciones
- Lista visual de todas tus sesiones
- Reproducir video o ver telemetría con 1 click
- No necesitas navegar por carpetas

### ✅ Análisis Rápido
- Estadísticas instantáneas al cargar telemetría
- Identifica bloqueos, velocidades, Gs sin abrir gráficos
- Visualizador web para análisis profundo

### ✅ Monitoreo en Tiempo Real
- Ve la duración de la grabación actual
- Contador de registros de telemetría
- Log detallado de todo lo que sucede

### ✅ Configuración Visual
- Cambia ajustes sin editar archivos
- Opciones claras y explicadas
- Guarda configuración fácilmente

---

## 📝 Flujo de Trabajo Típico

### 1️⃣ Preparación
```
- Abrir acc_recorder_gui.py
- Ir a pestaña "⚙️ Configuración"
- Ajustar FPS/Calidad si es necesario
- Volver a "🎮 Control de Grabación"
- Click "▶ Iniciar Servicio"
```

### 2️⃣ Durante la Carrera
```
- Iniciar ACC
- Comenzar sesión (Practice/Qualifying/Race)
- La grabación inicia automáticamente
- Ves el log en tiempo real
- Ves duración y registros aumentando
```

### 3️⃣ Después de la Carrera
```
- Grabación se detiene automáticamente
- Ir a pestaña "📁 Grabaciones"
- Seleccionar la sesión recién grabada
- Click "📊 Ver Telemetría"
- Revisar estadísticas rápidas
- Click "🌐 Abrir Visualizador Web" para gráficos
```

### 4️⃣ Análisis Profundo
```
- En visualizador web, cargar telemetry.json
- Usar slider para navegar por la vuelta
- Ver gráficos de bloqueos, Gs, temperaturas
- Identificar puntos de mejora
```

---

## 🆚 Comparación: Antes vs Ahora

| Característica | Antes | Ahora |
|----------------|-------|-------|
| **Interfaz** | Terminal/Consola | GUI moderna con pestañas |
| **Control** | Script separado | Botones integrados |
| **Ver grabaciones** | Explorador de archivos | Lista visual en la app |
| **Reproducir video** | Buscar archivo manualmente | 1 click en la lista |
| **Ver telemetría** | Abrir HTML separado | Cargador integrado + stats |
| **Configuración** | Editar config.py | GUI visual con opciones |
| **Monitoreo** | Solo log | Log + contador tiempo real |

---

## 🎯 Archivos del Proyecto

### Archivos Principales
- **`acc_recorder_gui.py`** ⭐ **NUEVA GUI INTEGRADA** - Usa este
- `acc_recorder.py` - Versión antigua (ya no necesaria)
- `acc_telemetry.py` - Módulo de telemetría (sin cambios)
- `telemetry_viewer.html` - Visualizador web con gráficos

### Scripts de Ejecución
- **`run_recorder.bat`** - Ahora ejecuta la nueva GUI
- `install.bat` - Instalación (sin cambios)

### Documentación
- `README.md` - Actualizado con nueva GUI
- `TROUBLESHOOTING.md` - Solución de problemas
- `NUEVA_GUI.md` - Este archivo

---

## 💡 Consejos de Uso

### Para Mejor Rendimiento
1. En Configuración, usa:
   - FPS: 30
   - CRF: 23
   - Preset: ultrafast
   - Intervalo: 1s

### Para Máxima Calidad
1. En Configuración, usa:
   - FPS: 60
   - CRF: 18
   - Preset: medium
   - Intervalo: 0.5s
   
⚠️ Requiere PC potente

### Para Analizar Bloqueos
1. Graba sesión
2. Ve a "📁 Grabaciones"
3. Click "📊 Ver Telemetría"
4. Busca sección "Primeros 10 bloqueos"
5. Anota los segundos
6. Abre visualizador web
7. Usa slider para ir a esos momentos exactos
8. Analiza gráfico de Wheel Slip

---

## 🐛 Problemas Conocidos

### "ModuleNotFoundError"
- Asegúrate de ejecutar con el entorno virtual activado
- Usa `run_recorder.bat` en lugar de ejecutar directamente

### "FFmpeg no encontrado"
- Ver TROUBLESHOOTING.md
- FFmpeg debe estar en PATH

### Grabaciones no aparecen en lista
- Click en "🔄 Actualizar Lista"
- Verifica que hay archivos .mp4 en las carpetas

---

## 🔜 Próximas Mejoras

Posibles adiciones futuras:
- [ ] Comparar 2 vueltas en el visualizador
- [ ] Exportar clips de momentos específicos
- [ ] Overlay de telemetría en el video
- [ ] Detección automática de incidentes
- [ ] Sincronización automática video-telemetría
- [ ] Gráfico de trazada en pista

---

**¡Disfruta de la nueva interfaz integrada!** 🏁
