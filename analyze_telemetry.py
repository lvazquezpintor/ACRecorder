"""
Herramienta para analizar archivos de telemetría grabados
"""

import json
from pathlib import Path
from datetime import datetime


def analyze_telemetry_file(telemetry_path: Path):
    """Analiza un archivo de telemetría y muestra estadísticas"""
    
    print("="*80)
    print(f"ANÁLISIS DE TELEMETRÍA: {telemetry_path.parent.name}")
    print("="*80)
    
    # Cargar datos
    with open(telemetry_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("❌ No hay datos en el archivo")
        return
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   Total de registros: {len(data)}")
    
    # Calcular duración
    if len(data) > 1:
        first_time = datetime.fromisoformat(data[0]['timestamp'])
        last_time = datetime.fromisoformat(data[-1]['timestamp'])
        duration = (last_time - first_time).total_seconds()
        print(f"   Duración: {duration:.1f} segundos ({duration/60:.1f} minutos)")
        print(f"   Frecuencia: {len(data)/duration:.1f} samples/segundo")
    
    # Analizar primer registro para ver estructura
    first_record = data[0]
    
    # Información del jugador
    player = first_record.get('player_telemetry', {})
    if player:
        print(f"\n🏎️  DATOS DEL JUGADOR:")
        print(f"   Velocidad máxima: {max([r.get('player_telemetry', {}).get('speed_kmh', 0) for r in data]):.1f} km/h")
        print(f"   RPM máximo: {max([r.get('player_telemetry', {}).get('rpm', 0) for r in data])}")
        
        # Temperaturas
        temps = [r.get('player_telemetry', {}).get('tyres', {}).get('temperature', {}) for r in data]
        if temps and temps[0]:
            max_temp_fl = max([t.get('front_left', 0) for t in temps if t])
            max_temp_fr = max([t.get('front_right', 0) for t in temps if t])
            print(f"   Temp. máxima neumáticos delanteros: {max(max_temp_fl, max_temp_fr):.1f}°C")
    
    # Información de sesión
    session = first_record.get('session_info', {})
    if session:
        print(f"\n📋 SESIÓN:")
        print(f"   Tipo: {session.get('session_type', 'Unknown')}")
        print(f"   Vueltas completadas: {session.get('completed_laps', 0)}")
        print(f"   Posición: {session.get('position', 'N/A')}")
    
    # Información del coche
    car_info = first_record.get('car_info', {})
    if car_info:
        print(f"\n🚗 COCHE:")
        print(f"   Modelo: {car_info.get('car_model', 'Unknown')}")
        print(f"   Piloto: {car_info.get('player_name', 'Unknown')}")
        print(f"   RPM máximo: {car_info.get('max_rpm', 0)}")
    
    # Información de pista
    track = first_record.get('track_data', {})
    if track:
        print(f"\n🏁 CIRCUITO:")
        print(f"   Nombre: {track.get('track_name', 'Unknown')}")
        print(f"   Longitud: {track.get('track_meters', 0)} metros")
    
    # Análisis de clasificación
    standings_available = any(r.get('standings') for r in data)
    
    if standings_available:
        print(f"\n🏆 CLASIFICACIÓN:")
        
        # Obtener clasificación del último registro con datos
        last_standings = None
        for record in reversed(data):
            if record.get('standings'):
                last_standings = record['standings']
                break
        
        if last_standings:
            print(f"   Total de pilotos: {len(last_standings)}")
            print(f"\n   Top 10:")
            print(f"   {'Pos':<5} {'Piloto':<30} {'#':<5} {'Vueltas':<8}")
            print(f"   {'-'*50}")
            
            for entry in last_standings[:10]:
                pos = entry.get('position', '?')
                name = entry.get('driver_name', 'Unknown')[:28]
                number = entry.get('car_number', '?')
                laps = entry.get('laps', 0)
                
                print(f"   {pos:<5} {name:<30} {number:<5} {laps:<8}")
            
            # Tu posición
            your_pos = session.get('position')
            if your_pos:
                print(f"\n   📍 Tu posición final: {your_pos}°")
    else:
        print(f"\n⚠️  Broadcasting no estaba habilitado - Sin datos de clasificación")
    
    # Resumen de archivos
    session_dir = telemetry_path.parent
    print(f"\n📁 ARCHIVOS EN LA SESIÓN:")
    for file in sorted(session_dir.glob('*')):
        size_kb = file.stat().st_size / 1024
        print(f"   • {file.name} ({size_kb:.1f} KB)")
    
    print("\n" + "="*80)


def list_sessions(recordings_dir: Path):
    """Lista todas las sesiones grabadas"""
    
    sessions = []
    for session_dir in recordings_dir.iterdir():
        if session_dir.is_dir():
            telemetry_file = session_dir / "telemetry.json"
            summary_file = session_dir / "summary.json"
            
            if telemetry_file.exists():
                sessions.append({
                    'name': session_dir.name,
                    'path': session_dir,
                    'telemetry': telemetry_file,
                    'has_summary': summary_file.exists()
                })
    
    return sorted(sessions, key=lambda x: x['name'], reverse=True)


def main():
    recordings_dir = Path("recordings")
    
    if not recordings_dir.exists():
        print("❌ No existe el directorio 'recordings'")
        print("   Ejecuta primero test_recording.py para grabar datos")
        return
    
    # Listar sesiones disponibles
    sessions = list_sessions(recordings_dir)
    
    if not sessions:
        print("❌ No hay sesiones grabadas")
        print("   Ejecuta test_recording.py para crear una grabación")
        return
    
    print("📂 SESIONES DISPONIBLES:")
    print()
    
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session['name']}")
        if session['has_summary']:
            summary_path = session['path'] / "summary.json"
            with open(summary_path, 'r') as f:
                summary = json.load(f)
            print(f"   ⏱️  {summary.get('duration_seconds', 0):.1f}s | "
                  f"📝 {summary.get('records_count', 0)} registros | "
                  f"📡 Broadcasting: {'✓' if summary.get('broadcasting_enabled') else '✗'}")
        print()
    
    # Seleccionar sesión
    try:
        choice = input("Selecciona una sesión para analizar (número o 'q' para salir): ")
        
        if choice.lower() == 'q':
            return
        
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            selected = sessions[idx]
            print()
            analyze_telemetry_file(selected['telemetry'])
        else:
            print("❌ Selección inválida")
    
    except ValueError:
        print("❌ Entrada inválida")
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado")


if __name__ == "__main__":
    main()
