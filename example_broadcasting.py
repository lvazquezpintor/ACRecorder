"""
Ejemplo de uso del Broadcasting SDK integrado con Shared Memory
Muestra cómo obtener telemetría completa de ACC incluyendo posiciones de pilotos
"""

from core.acc_telemetry import ACCTelemetry
from core.broadcasting import ACCBroadcastingClient
import time
import json


def main():
    print("=== ACC Recorder - Broadcasting + Shared Memory ===\n")
    
    # 1. CONFIGURAR BROADCASTING
    print("PASO 1: Configurar Broadcasting en ACC")
    print("Edita: Documents\\Assetto Corsa Competizione\\Config\\broadcasting.json")
    print("""
{
    "updListenerPort": 9000,
    "connectionPassword": "asd",
    "commandPassword": ""
}
    """)
    input("Presiona ENTER cuando hayas configurado broadcasting.json...")
    
    # 2. CONECTAR A SHARED MEMORY
    print("\nConectando a Shared Memory...")
    telemetry = ACCTelemetry()
    
    if not telemetry.connect():
        print("❌ Error: No se pudo conectar a Shared Memory")
        print("Asegúrate de que ACC esté corriendo")
        return
    
    print("✅ Conectado a Shared Memory")
    
    # 3. CONECTAR A BROADCASTING
    print("\nConectando a Broadcasting SDK...")
    broadcasting = ACCBroadcastingClient()
    
    if not broadcasting.connect(
        display_name="ACCRecorder",
        ip="127.0.0.1",
        port=9000,
        password="asd",
        update_interval_ms=250
    ):
        print("❌ Error: No se pudo conectar al Broadcasting")
        print("Verifica que ACC esté corriendo y broadcasting.json esté configurado")
        telemetry.disconnect()
        return
    
    print("✅ Conectado al Broadcasting SDK")
    
    # 4. ESPERAR A QUE SE RECIBAN DATOS
    print("\n⏳ Esperando datos... (entra en una sesión en ACC)")
    time.sleep(2)
    
    # 5. OBTENER Y MOSTRAR DATOS
    print("\n" + "="*80)
    print("DATOS DE TELEMETRÍA COMBINADOS")
    print("="*80 + "\n")
    
    try:
        while True:
            # Datos de tu coche (Shared Memory)
            player_data = telemetry.get_player_telemetry()
            session_info = telemetry.get_session_info()
            car_info = telemetry.get_car_info()
            
            # Datos de todos los coches (Broadcasting)
            standings = broadcasting.get_standings()
            track_data = broadcasting.get_track_data()
            broadcast_session = broadcasting.get_session_info()
            
            # Limpiar pantalla
            print("\033[H\033[J", end="")
            
            # MOSTRAR INFORMACIÓN DE SESIÓN
            if session_info:
                print(f"📊 SESIÓN: {session_info.get('session_type', 'Unknown')}")
                print(f"⏱️  Tiempo restante: {session_info.get('session_time_left', 0):.1f}s")
                print(f"🏁 Vueltas completadas: {session_info.get('completed_laps', 0)}")
                print()
            
            # MOSTRAR INFORMACIÓN DEL CIRCUITO
            if track_data:
                print(f"🏎️  Circuito: {track_data.get('track_name', 'Unknown')}")
                print(f"📏 Longitud: {track_data.get('track_meters', 0)} metros")
                print()
            
            # MOSTRAR TU TELEMETRÍA
            if player_data:
                print("🎮 TU COCHE:")
                print(f"   Velocidad: {player_data.get('speed_kmh', 0):.1f} km/h")
                print(f"   Marcha: {player_data.get('gear', 0)}")
                print(f"   RPM: {player_data.get('rpm', 0)}")
                print(f"   Acelerador: {player_data.get('gas', 0)*100:.0f}%")
                print(f"   Freno: {player_data.get('brake', 0)*100:.0f}%")
                
                # Temperaturas de neumáticos
                tyres = player_data.get('tyres', {})
                temps = tyres.get('temperature', {})
                print(f"\n   🌡️  Temperaturas neumáticos:")
                print(f"      FL: {temps.get('front_left', 0):.1f}°C  FR: {temps.get('front_right', 0):.1f}°C")
                print(f"      RL: {temps.get('rear_left', 0):.1f}°C   RR: {temps.get('rear_right', 0):.1f}°C")
                
                # Presiones de neumáticos
                pressures = tyres.get('pressure', {})
                print(f"\n   📊 Presiones neumáticos:")
                print(f"      FL: {pressures.get('front_left', 0):.2f} PSI  FR: {pressures.get('front_right', 0):.2f} PSI")
                print(f"      RL: {pressures.get('rear_left', 0):.2f} PSI   RR: {pressures.get('rear_right', 0):.2f} PSI")
                print()
            
            # MOSTRAR CLASIFICACIÓN
            if standings:
                print("🏆 CLASIFICACIÓN:")
                print("-" * 80)
                print(f"{'Pos':<5} {'Piloto':<30} {'#':<5} {'Vueltas':<8} {'Delta':<10}")
                print("-" * 80)
                
                for entry in standings[:10]:  # Mostrar top 10
                    pos = entry['position']
                    name = entry['driver_name'][:28]
                    number = entry['car_number']
                    laps = entry['laps']
                    delta_ms = entry['delta']
                    delta_str = f"+{delta_ms/1000:.3f}s" if delta_ms > 0 else "Leader"
                    
                    print(f"{pos:<5} {name:<30} {number:<5} {laps:<8} {delta_str:<10}")
                
                if len(standings) > 10:
                    print(f"\n... y {len(standings) - 10} pilotos más")
            else:
                print("⏳ Esperando datos de clasificación...")
            
            print("\n" + "="*80)
            print("Presiona Ctrl+C para salir")
            
            # Esperar antes de actualizar
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo...")
    
    finally:
        # 6. DESCONECTAR
        broadcasting.disconnect()
        telemetry.disconnect()
        print("✅ Desconectado correctamente")


def save_telemetry_with_standings():
    """
    Ejemplo de cómo guardar telemetría con standings en JSON
    """
    telemetry = ACCTelemetry()
    broadcasting = ACCBroadcastingClient()
    
    telemetry.connect()
    broadcasting.connect(password="asd")
    
    time.sleep(2)  # Esperar datos
    
    # Recopilar todos los datos
    data_snapshot = {
        'timestamp': time.time(),
        'player_telemetry': telemetry.get_player_telemetry(),
        'session_info': telemetry.get_session_info(),
        'car_info': telemetry.get_car_info(),
        'standings': broadcasting.get_standings(),
        'track_data': broadcasting.get_track_data(),
        'broadcast_session': broadcasting.get_session_info()
    }
    
    # Guardar en JSON
    filename = f"telemetry_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_snapshot, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Telemetría guardada en: {filename}")
    
    broadcasting.disconnect()
    telemetry.disconnect()


if __name__ == "__main__":
    main()
