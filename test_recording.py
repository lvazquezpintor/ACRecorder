"""
Script de prueba para grabar telemetría de ACC con Broadcasting
"""

from pathlib import Path
from core.telemetry_recorder import TelemetryRecorder
import time


def main():
    print("="*80)
    print("ACC TELEMETRY RECORDER - Prueba de Grabación")
    print("="*80)
    
    # Instrucciones
    print("\n📋 ANTES DE EMPEZAR:")
    print("1. Configura Broadcasting en ACC:")
    print("   Edita: Documents\\Assetto Corsa Competizione\\Config\\broadcasting.json")
    print("""
   {
       "updListenerPort": 9000,
       "connectionPassword": "asd",
       "commandPassword": ""
   }
    """)
    print("2. Reinicia ACC si acabas de editar el archivo")
    print("3. Entra en una sesión (práctica, clasificación o carrera)")
    
    input("\nPresiona ENTER cuando estés listo...")
    
    # Crear directorio de salida
    output_dir = Path("recordings")
    output_dir.mkdir(exist_ok=True)
    
    # Crear grabador con Broadcasting habilitado
    recorder = TelemetryRecorder(
        output_dir=output_dir,
        enable_broadcasting=True  # ¡Importante! Esto habilita las posiciones
    )
    
    # Configurar callbacks para ver el progreso
    def on_started(session_name):
        print(f"\n🎬 Grabación iniciada: {session_name}")
    
    def on_update(data):
        # Mostrar info cada 10 registros
        if len(recorder.telemetry_data) % 10 == 0:
            player = data.get('player_telemetry', {})
            standings = data.get('standings', [])
            
            print(f"\r📊 Registros: {len(recorder.telemetry_data)} | "
                  f"Velocidad: {player.get('speed_kmh', 0):.0f} km/h | "
                  f"Pilotos: {len(standings)}", end='')
    
    def on_stopped(records, duration):
        print(f"\n\n✅ Grabación finalizada!")
        print(f"   📝 Registros: {records}")
        print(f"   ⏱️  Duración: {duration:.1f}s")
    
    recorder.on_recording_started = on_started
    recorder.on_telemetry_update = on_update
    recorder.on_recording_stopped = on_stopped
    
    try:
        # Iniciar grabación
        print("\n🔌 Conectando a ACC...")
        session_dir = recorder.start_recording()
        
        print("\n⏺️  GRABANDO... (Presiona Ctrl+C para detener)")
        print("   Corre algunas vueltas en ACC para capturar datos\n")
        
        # Grabar durante un tiempo o hasta que se presione Ctrl+C
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo grabación...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # Detener grabación
        records, duration = recorder.stop_recording()
        
        if records > 0:
            print(f"\n📂 Archivos guardados en: {session_dir}")
            print("\n📄 Archivos creados:")
            print(f"   • session_info.json - Información de la sesión")
            print(f"   • telemetry.json - Datos completos de telemetría")
            print(f"   • summary.json - Resumen de la grabación")
            
            # Exportar a CSV si hay datos
            try:
                csv_file = session_dir / "telemetry.csv"
                recorder.export_csv(csv_file)
                print(f"   • telemetry.csv - Telemetría en formato CSV")
                
                # Exportar clasificación si está disponible
                if recorder.telemetry_data and recorder.telemetry_data[0].get('standings'):
                    standings_csv = session_dir / "standings.csv"
                    recorder.export_standings_csv(standings_csv)
                    print(f"   • standings.csv - Clasificación de pilotos")
            except Exception as e:
                print(f"   ⚠️  No se pudieron crear los CSV: {e}")
        
        # Desconectar
        recorder.disconnect_from_acc()
        print("\n👋 Hasta luego!")


if __name__ == "__main__":
    main()
