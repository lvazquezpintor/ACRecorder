# ACC Recorder - Estructura Modular

## 📁 Estructura del Proyecto

```
ACRecorder/
├── acc_recorder_qt_modular.py    # ⭐ Punto de entrada (ejecutar este)
├── gui/
│   ├── __init__.py
│   ├── main_window.py            # Ventana principal + lógica de negocio
│   ├── widgets.py                # Componentes reutilizables
│   ├── styles.py                 # Colores y estilos centralizados
│   └── tabs/
│       ├── __init__.py
│       ├── control_tab.py        # 🏁 Pestaña Control
│       ├── sessions_tab.py       # 📄 Pestaña Sessions
│       ├── analytics_tab.py      # 📊 Pestaña Analytics
│       └── settings_tab.py       # ⚙️ Pestaña Settings
├── core/
│   ├── __init__.py
│   ├── recorder.py               # (Futuro) Lógica de grabación
│   └── telemetry.py              # (Futuro) Lógica de telemetría
├── acc_telemetry.py              # Módulo de telemetría ACC
├── config.json                   # Configuración guardada
└── requirements.txt
```

## 🚀 Cómo Ejecutar

```bash
# Instalar dependencias
pip install PySide6 psutil

# Ejecutar la aplicación MODULAR
python acc_recorder_qt_modular.py
```

## 🎯 Ventajas de Esta Estructura

### ✅ Mantenibilidad
- **Cada pestaña en su propio archivo** - Fácil de modificar sin tocar el resto
- **Widgets reutilizables** - DRY (Don't Repeat Yourself)
- **Estilos centralizados** - Cambiar colores en un solo lugar

### ✅ Escalabilidad
- Fácil añadir nuevas pestañas
- Separación clara de responsabilidades
- Preparado para testing

### ✅ Colaboración
- Múltiples personas pueden trabajar en diferentes pestañas
- Conflictos de Git minimizados
- Code reviews más fáciles

## 📝 Modificar una Pestaña

### Ejemplo: Modificar la pestaña de Control

```bash
# Solo necesitas editar este archivo:
gui/tabs/control_tab.py
```

No necesitas tocar:
- ❌ main_window.py
- ❌ Otras pestañas
- ❌ Widgets compartidos

### Ejemplo: Cambiar colores globales

```bash
# Editar:
gui/styles.py

# Los cambios se aplican automáticamente a toda la app
```

## 🔌 Sistema de Señales (Signals)

Las pestañas se comunican mediante señales de Qt:

```python
# control_tab.py emite:
start_monitoring_requested = Signal()

# main_window.py escucha:
self.control_tab.start_monitoring_requested.connect(self.start_monitoring)
```

Esto mantiene las pestañas **desacopladas** y **reutilizables**.

## 📦 Archivos Principales

### acc_recorder_qt_modular.py (23 líneas)
Punto de entrada ultra-simple. Solo inicializa la app.

### gui/main_window.py (300 líneas)
Ventana principal que:
- Crea el sidebar
- Gestiona las pestañas
- Contiene la lógica de monitoreo/grabación
- Coordina la comunicación entre pestañas

### gui/tabs/control_tab.py (150 líneas)
Pestaña de control que:
- Muestra el estado del sistema
- Botones START/STOP
- Log de eventos
- Cards de datos

### gui/tabs/sessions_tab.py (180 líneas)
Pestaña de sesiones que:
- Lista grabaciones
- Reproduce videos
- Abre carpetas
- Cambia a Analytics

### gui/tabs/analytics_tab.py (120 líneas)
Pestaña de análisis que:
- Carga archivos JSON
- Genera estadísticas
- Abre visualizador web

### gui/tabs/settings_tab.py (180 líneas)
Pestaña de configuración que:
- Ajustes de video (FPS, CRF, Preset)
- Ajustes de telemetría (Intervalo)
- Directorio de salida
- Guardar configuración

## 🎨 Personalización

### Cambiar el tema de colores

Edita `gui/styles.py`:

```python
COLORS = {
    'accent_red': '#E53E3E',  # Cambiar a tu color
    # ... más colores
}
```

### Añadir una nueva pestaña

1. Crear `gui/tabs/nueva_tab.py`
2. Heredar de `QWidget`
3. Implementar `setup_ui()`
4. Añadir a `main_window.py`:

```python
from gui.tabs.nueva_tab import NuevaTab

# En create_content_area():
self.nueva_tab = NuevaTab()
self.pages.addWidget(self.nueva_tab)
```

## 🐛 Debug

Cada pestaña puede usar logs independientes:

```python
# En control_tab.py
self.log("Mi mensaje de debug")
```

## 📚 Próximos Pasos

- [ ] Mover lógica de grabación a `core/recorder.py`
- [ ] Mover lógica de telemetría a `core/telemetry.py`
- [ ] Añadir tests unitarios por pestaña
- [ ] Documentación de API de cada componente

---

**Creado con la skill `python-patterns` aplicando principios de:**
- ✅ Separación de responsabilidades
- ✅ Organización por features
- ✅ Código mantenible y escalable
