"""
Ejemplos de uso de los módulos de grabación refactorizados

Este archivo demuestra cómo usar TelemetryRecorder y ScreenRecorder
de forma independiente o combinada.
"""

from pathlib import Path
from datetime import datetime
import time
import random

from core import TelemetryRecorder, ScreenRecorder


# =============================================================================
# EJEMPLO 1: Grabación de telemetría simple
# =============================================================================

def ejemplo_telemetria_basico():
    """Ejemplo básico de grabación de telemetría"""
    print("=== EJEMPLO 1: Telemetría Básica ===\n")
    
    # Crear directorio de salida
    output_dir = Path("./ejemplos_output")
    output_dir.mkdir(exist_ok=True)
    
    # Inicializar grabador
    recorder = TelemetryRecorder(output_dir)
    
    # Iniciar grabación
    print("Iniciando grabación de telemetría...")
    session_dir = recorder.start_recording("ejemplo_basico")
    print(f"Sesión creada en: {session_dir}\n")
    
    # Simular 5 segundos de telemetría
    for i in range(5):
        data = {
            'speed': random.uniform(80, 200),
            'rpm': random.randint(3000, 9000),
            'gear': random.randint(1, 6),
            'throttle': random.uniform(0, 1),
            'brake': random.uniform(0, 1)
        }
        recorder.add_telemetry_record(data)
        print(f"Registro {i+1}: Speed={data['speed']:.1f} km/h, RPM={data['rpm']}")
        time.sleep(1)
    
    # Detener y obtener estadísticas
    print("\nDeteniendo grabación...")
    records, duration = recorder.stop_recording()
    print(f"✓ Grabación completada: {records} registros en {duration:.1f}s\n")


# =============================================================================
# EJEMPLO 2: Telemetría con callbacks
# =============================================================================

def ejemplo_telemetria_callbacks():
    """Ejemplo de telemetría con callbacks para monitoreo en tiempo real"""
    print("=== EJEMPLO 2: Telemetría con Callbacks ===\n")
    
    output_dir = Path("./ejemplos_output")
    recorder = TelemetryRecorder(output_dir)
    
    # Configurar callbacks
    def on_started(session_name):
        print(f"🟢 Grabación iniciada: {session_name}")
    
    def on_stopped(count, duration):
        print(f"\n🔴 Grabación finalizada: {count} registros, {duration:.1f}s")
    
    def on_update(data):
        # Mostrar advertencia si RPM es muy alto
        if data.get('rpm', 0) > 8500:
            print(f"⚠️  RPM ALTO: {data['rpm']} RPM!")
    
    recorder.on_recording_started = on_started
    recorder.on_recording_stopped = on_stopped
    recorder.on_telemetry_update = on_update
    
    # Iniciar grabación
    recorder.start_recording("ejemplo_callbacks")
    
    # Simular telemetría
    for i in range(10):
        data = {
            'rpm': random.randint(3000, 9500),
            'speed': random.uniform(100, 250)
        }
        recorder.add_telemetry_record(data)
        time.sleep(0.5)
    
    # Detener
    recorder.stop_recording()
    print()


# =============================================================================
# EJEMPLO 3: Exportar telemetría a CSV
# =============================================================================

def ejemplo_exportar_csv():
    """Ejemplo de exportación de telemetría a CSV"""
    print("=== EJEMPLO 3: Exportar a CSV ===\n")
    
    output_dir = Path("./ejemplos_output")
    recorder = TelemetryRecorder(output_dir)
    
    # Grabar algunos datos
    print("Grabando datos de telemetría...")
    recorder.start_recording("ejemplo_csv")
    
    for i in range(20):
        data = {
            'time': i,
            'speed': 100 + i * 5,
            'rpm': 4000 + i * 200,
            'gear': min(6, 1 + i // 4),
            'throttle': min(1.0, i * 0.05),
            'brake': 0.0
        }
        recorder.add_telemetry_record(data)
    
    recorder.stop_recording()
    
    # Exportar a CSV
    csv_file = output_dir / "telemetria_ejemplo.csv"
    print(f"\nExportando a CSV: {csv_file}")
    recorder.export_csv(csv_file, fields=['time', 'speed', 'rpm', 'gear'])
    print("✓ CSV creado exitosamente\n")


# =============================================================================
# EJEMPLO 4: Grabación de pantalla básica (requiere ffmpeg)
# =============================================================================

def ejemplo_screen_basico():
    """Ejemplo básico de grabación de pantalla"""
    print("=== EJEMPLO 4: Grabación de Pantalla Básica ===\n")
    
    output_dir = Path("./ejemplos_output")
    recorder = ScreenRecorder(output_dir)
    
    # Verificar que ffmpeg esté disponible
    if not recorder._check_ffmpeg():
        print("❌ ffmpeg no está instalado. Saltando ejemplo.\n")
        return
    
    # Configurar grabación
    recorder.configure(
        fps=30,
        preset='ultrafast',
        crf=28,  # Mayor CRF = menor calidad, menor tamaño
        audio=False  # Desactivar audio para el ejemplo
    )
    
    print("Iniciando grabación de pantalla por 5 segundos...")
    print("(Mueve el mouse o haz algo visible en pantalla)\n")
    
    # Callbacks
    recorder.on_recording_started = lambda path: print(f"🎥 Grabando en: {Path(path).name}")
    recorder.on_recording_stopped = lambda dur: print(f"✓ Grabación completada: {dur:.1f}s")
    recorder.on_error = lambda msg: print(f"❌ Error: {msg}")
    
    # Grabar
    try:
        recorder.start_recording("ejemplo_screen.mp4")
        time.sleep(5)
        recorder.stop_recording()
    except Exception as e:
        print(f"Error durante la grabación: {e}")
    
    print()


# =============================================================================
# EJEMPLO 5: Telemetría + Pantalla sincronizadas
# =============================================================================

def ejemplo_combinado():
    """Ejemplo de grabación combinada de telemetría y pantalla"""
    print("=== EJEMPLO 5: Grabación Combinada ===\n")
    
    output_dir = Path("./ejemplos_output")
    
    # Crear ambos grabadores
    telemetry = TelemetryRecorder(output_dir)
    screen = ScreenRecorder(output_dir)
    
    # Verificar ffmpeg
    if not screen._check_ffmpeg():
        print("❌ ffmpeg no está instalado. Solo grabará telemetría.\n")
        screen = None
    
    # Configurar
    if screen:
        screen.configure(fps=30, preset='ultrafast', audio=False)
    
    # Nombre de sesión común
    session_name = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    
    print(f"Iniciando grabación combinada: {session_name}")
    print("Duración: 5 segundos\n")
    
    # Iniciar ambas grabaciones
    telemetry.start_recording(session_name)
    if screen:
        screen.start_recording(f"{session_name}.mp4")
    
    # Simular telemetría durante la grabación
    for i in range(50):  # 50 registros en 5 segundos
        data = {
            'frame': i,
            'speed': 150 + random.uniform(-20, 20),
            'rpm': 7000 + random.randint(-500, 500),
            'gear': random.randint(3, 5)
        }
        telemetry.add_telemetry_record(data)
        time.sleep(0.1)
    
    # Detener ambas grabaciones
    print("\nDeteniendo grabaciones...")
    if screen:
        screen.stop_recording()
    records, duration = telemetry.stop_recording()
    
    print(f"✓ Telemetría: {records} registros")
    print(f"✓ Duración total: {duration:.1f}s\n")


# =============================================================================
# EJEMPLO 6: Monitorear estadísticas en tiempo real
# =============================================================================

def ejemplo_estadisticas_tiempo_real():
    """Ejemplo de monitoreo de estadísticas durante la grabación"""
    print("=== EJEMPLO 6: Estadísticas en Tiempo Real ===\n")
    
    output_dir = Path("./ejemplos_output")
    recorder = TelemetryRecorder(output_dir)
    
    # Iniciar grabación
    recorder.start_recording("ejemplo_stats")
    
    # Simular grabación con monitoreo
    print("Grabando... (mostrando estadísticas cada segundo)\n")
    for i in range(5):
        # Añadir algunos datos
        for j in range(10):
            data = {
                'iteration': i * 10 + j,
                'value': random.random()
            }
            recorder.add_telemetry_record(data)
        
        # Obtener y mostrar estadísticas
        stats = recorder.get_current_stats()
        print(f"Segundo {i+1}:")
        print(f"  - Grabando: {stats['is_recording']}")
        print(f"  - Registros: {stats['records_count']}")
        print(f"  - Duración: {stats['duration']:.1f}s")
        print()
        
        time.sleep(1)
    
    # Detener
    recorder.stop_recording()


# =============================================================================
# MAIN: Ejecutar todos los ejemplos
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("EJEMPLOS DE USO - MÓDULOS DE GRABACIÓN REFACTORIZADOS")
    print("="*70 + "\n")
    
    # Ejecutar ejemplos
    try:
        ejemplo_telemetria_basico()
        time.sleep(1)
        
        ejemplo_telemetria_callbacks()
        time.sleep(1)
        
        ejemplo_exportar_csv()
        time.sleep(1)
        
        ejemplo_screen_basico()
        time.sleep(1)
        
        ejemplo_combinado()
        time.sleep(1)
        
        ejemplo_estadisticas_tiempo_real()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejemplos interrumpidos por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante los ejemplos: {e}")
    
    print("\n" + "="*70)
    print("FIN DE LOS EJEMPLOS")
    print("="*70 + "\n")
    print("Los archivos generados están en: ./ejemplos_output/")
    print()
