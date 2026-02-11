#!/usr/bin/env python3
"""
Script de diagnóstico para grabación de pantalla en macOS

Este script te ayudará a identificar problemas con la grabación de pantalla
y te dará instrucciones específicas para solucionarlos.
"""

import subprocess
import platform
from pathlib import Path


def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def check_macos():
    """Verifica que estemos en macOS"""
    if platform.system() != 'Darwin':
        print("❌ Este script es solo para macOS")
        print(f"   Sistema actual: {platform.system()}")
        return False
    
    print("✅ Sistema: macOS")
    print(f"   Versión: {platform.mac_ver()[0]}")
    return True


def check_ffmpeg():
    """Verifica la instalación de ffmpeg"""
    print_header("1. VERIFICANDO FFMPEG")
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        output = result.stdout.decode('utf-8')
        version_line = output.split('\n')[0]
        print(f"✅ ffmpeg instalado: {version_line}")
        return True
        
    except FileNotFoundError:
        print("❌ ffmpeg NO está instalado")
        print("\n📝 Para instalar ffmpeg en macOS:")
        print("   1. Instala Homebrew si no lo tienes:")
        print("      /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("\n   2. Instala ffmpeg:")
        print("      brew install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ Error al verificar ffmpeg: {e}")
        return False


def list_avfoundation_devices():
    """Lista los dispositivos disponibles en avfoundation"""
    print_header("2. DISPOSITIVOS DISPONIBLES")
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        output = result.stderr.decode('utf-8', errors='ignore')
        
        print("\n📹 DISPOSITIVOS DE VIDEO:")
        video_section = False
        audio_section = False
        
        for line in output.split('\n'):
            if 'AVFoundation video devices:' in line:
                video_section = True
                audio_section = False
                continue
            elif 'AVFoundation audio devices:' in line:
                video_section = False
                audio_section = True
                print("\n🔊 DISPOSITIVOS DE AUDIO:")
                continue
            
            if video_section or audio_section:
                if '[AVFoundation' in line and ']' in line:
                    # Extraer índice y nombre
                    parts = line.split(']')
                    if len(parts) >= 2:
                        index = parts[0].split('[')[-1]
                        name = parts[1].strip()
                        
                        if video_section:
                            icon = "🖥️" if "screen" in name.lower() else "📷"
                        else:
                            icon = "🎤"
                        
                        print(f"   [{index}] {icon} {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al listar dispositivos: {e}")
        return False


def check_screen_recording_permission():
    """Verifica los permisos de grabación de pantalla"""
    print_header("3. PERMISOS DE GRABACIÓN DE PANTALLA")
    
    print("\n⚠️  En macOS, las aplicaciones necesitan permiso explícito para grabar la pantalla.")
    print("\n📝 Para verificar/otorgar permisos:")
    print("   1. Abre 'Preferencias del Sistema' (System Settings)")
    print("   2. Ve a 'Privacidad y Seguridad' (Privacy & Security)")
    print("   3. Selecciona 'Grabación de Pantalla' (Screen Recording)")
    print("   4. Asegúrate de que Python/Terminal/tu aplicación esté en la lista y marcada")
    print("\n💡 Si acabas de otorgar permisos, es posible que necesites:")
    print("   - Reiniciar la aplicación")
    print("   - Reiniciar Terminal si estás usando Python desde Terminal")
    print("   - En algunos casos, cerrar sesión y volver a entrar")
    
    return True


def test_basic_recording():
    """Prueba una grabación básica de 3 segundos"""
    print_header("4. PRUEBA DE GRABACIÓN")
    
    output_file = Path.home() / "Desktop" / "test_recording.mp4"
    
    print(f"\n🎬 Intentando grabar 3 segundos de pantalla...")
    print(f"   Archivo de salida: {output_file}")
    
    # Comando básico de ffmpeg para macOS
    cmd = [
        'ffmpeg',
        '-y',  # Sobrescribir sin preguntar
        '-f', 'avfoundation',
        '-framerate', '30',
        '-capture_cursor', '1',
        '-capture_mouse_clicks', '1',
        '-i', '1',  # Dispositivo 1 (generalmente pantalla principal)
        '-t', '3',  # Duración: 3 segundos
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p',
        str(output_file)
    ]
    
    print(f"\n📝 Comando a ejecutar:")
    print(f"   {' '.join(cmd)}")
    
    try:
        print("\n⏳ Grabando... (mueve el mouse en pantalla)")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        if result.returncode == 0 and output_file.exists():
            size = output_file.stat().st_size
            print(f"\n✅ ¡Grabación exitosa!")
            print(f"   Archivo creado: {output_file}")
            print(f"   Tamaño: {size / 1024:.1f} KB")
            print(f"\n💡 Puedes reproducir el video con:")
            print(f"   open {output_file}")
            return True
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"\n❌ La grabación falló")
            print(f"\n📋 Error de ffmpeg:")
            print("   " + "\n   ".join(stderr.split('\n')[-20:]))
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ Timeout - ffmpeg no respondió en 10 segundos")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_with_audio():
    """Prueba grabación con audio"""
    print_header("5. PRUEBA DE GRABACIÓN CON AUDIO")
    
    output_file = Path.home() / "Desktop" / "test_recording_audio.mp4"
    
    print(f"\n🎬 Intentando grabar 3 segundos con audio...")
    print(f"   Archivo de salida: {output_file}")
    
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'avfoundation',
        '-framerate', '30',
        '-capture_cursor', '1',
        '-i', '1:0',  # Pantalla:Audio
        '-t', '3',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        str(output_file)
    ]
    
    print(f"\n📝 Comando:")
    print(f"   {' '.join(cmd)}")
    
    try:
        print("\n⏳ Grabando...")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        if result.returncode == 0 and output_file.exists():
            print(f"\n✅ ¡Grabación con audio exitosa!")
            print(f"   Archivo: {output_file}")
            return True
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"\n⚠️  La grabación con audio falló")
            print(f"   Esto es común si no hay dispositivos de audio disponibles")
            print(f"   o si no se han otorgado permisos de micrófono")
            print(f"\n   Puedes grabar sin audio usando audio=False en la configuración")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    print("\n" + "🔍 DIAGNÓSTICO DE GRABACIÓN DE PANTALLA EN macOS")
    
    # 1. Verificar macOS
    if not check_macos():
        return
    
    # 2. Verificar ffmpeg
    if not check_ffmpeg():
        return
    
    # 3. Listar dispositivos
    list_avfoundation_devices()
    
    # 4. Verificar permisos
    check_screen_recording_permission()
    
    # 5. Prueba básica
    input("\n⏸️  Presiona Enter para hacer una prueba de grabación...")
    basic_ok = test_basic_recording()
    
    # 6. Prueba con audio
    if basic_ok:
        input("\n⏸️  Presiona Enter para probar grabación con audio...")
        test_with_audio()
    
    # Resumen final
    print_header("RESUMEN Y RECOMENDACIONES")
    
    if basic_ok:
        print("\n✅ La grabación de pantalla funciona correctamente")
        print("\n💡 Recomendaciones:")
        print("   - Usa audio=False si la grabación con audio falla")
        print("   - En macOS, usa preset='ultrafast' o 'veryfast' para mejor rendimiento")
        print("   - Si el video se ve mal, prueba crf=18 para mejor calidad")
    else:
        print("\n❌ La grabación de pantalla tiene problemas")
        print("\n🔧 Posibles soluciones:")
        print("   1. Verifica los permisos en Preferencias del Sistema")
        print("   2. Reinicia la aplicación después de otorgar permisos")
        print("   3. Intenta con un índice de dispositivo diferente (0, 1, 2...)")
        print("   4. Revisa los errores de ffmpeg mostrados arriba")
    
    print("\n" + "=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnóstico cancelado por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()
