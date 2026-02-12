#!/usr/bin/env python3
"""
Script de diagnóstico para grabación de pantalla en Windows

Este script te ayudará a identificar problemas con la grabación de pantalla
y te dará instrucciones específicas para solucionarlos.
"""

import subprocess
import platform
from pathlib import Path
import sys


def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def check_windows():
    """Verifica que estemos en Windows"""
    if platform.system() != 'Windows':
        print("❌ Este script es solo para Windows")
        print(f"   Sistema actual: {platform.system()}")
        return False
    
    print("✅ Sistema: Windows")
    print(f"   Versión: {platform.platform()}")
    return True


def check_ffmpeg():
    """Verifica la instalación de ffmpeg"""
    print_header("1. VERIFICANDO FFMPEG")
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = result.stdout.decode('utf-8')
        version_line = output.split('\n')[0]
        print(f"✅ ffmpeg instalado: {version_line}")
        return True
        
    except FileNotFoundError:
        print("❌ ffmpeg NO está instalado o no está en el PATH")
        print("\n📝 Para instalar ffmpeg en Windows:")
        print("\n   OPCIÓN 1: Con Chocolatey (recomendado)")
        print("   1. Abre PowerShell como Administrador")
        print("   2. Ejecuta: choco install ffmpeg")
        print("\n   OPCIÓN 2: Con Scoop")
        print("   1. Abre PowerShell")
        print("   2. Ejecuta: scoop install ffmpeg")
        print("\n   OPCIÓN 3: Instalación manual")
        print("   1. Descarga ffmpeg desde: https://www.gyan.dev/ffmpeg/builds/")
        print("   2. Extrae el archivo ZIP")
        print("   3. Añade la carpeta 'bin' al PATH del sistema:")
        print("      - Busca 'Variables de entorno' en el menú Inicio")
        print("      - Edita la variable 'Path'")
        print("      - Añade la ruta a la carpeta 'bin' de ffmpeg")
        print("   4. Reinicia la terminal/aplicación")
        return False
    except Exception as e:
        print(f"❌ Error al verificar ffmpeg: {e}")
        return False


def list_gdigrab_info():
    """Muestra información sobre gdigrab (captura de pantalla en Windows)"""
    print_header("2. INFORMACIÓN DE CAPTURA DE PANTALLA")
    
    print("\n📹 Windows usa 'gdigrab' para capturar la pantalla")
    print("\n   Opciones de captura:")
    print("   • 'desktop' - Captura toda la pantalla principal")
    print("   • 'video=screen-capture-recorder' - Alternativa (requiere software adicional)")
    print("\n   La aplicación usará 'desktop' por defecto")
    
    return True


def list_audio_devices():
    """Lista los dispositivos de audio disponibles con dshow"""
    print_header("3. DISPOSITIVOS DE AUDIO")
    
    print("\n🔊 Intentando listar dispositivos de audio...")
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = result.stderr.decode('utf-8', errors='ignore')
        
        print("\n📋 Dispositivos detectados:")
        in_audio = False
        audio_devices = []
        
        for line in output.split('\n'):
            if 'DirectShow audio devices' in line:
                in_audio = True
                continue
            elif 'DirectShow video devices' in line:
                in_audio = False
                continue
            
            if in_audio and '"' in line:
                # Extraer nombre del dispositivo
                device_name = line.split('"')[1] if '"' in line else line.strip()
                if device_name:
                    audio_devices.append(device_name)
                    print(f"   🎤 {device_name}")
        
        if not audio_devices:
            print("   ⚠️  No se detectaron dispositivos de audio")
            print("   Esto es normal si no hay micrófono conectado")
            print("   Puedes grabar sin audio usando audio=False")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al listar dispositivos de audio: {e}")
        print("   Esto no es crítico - puedes grabar sin audio")
        return False


def test_basic_recording():
    """Prueba una grabación básica de 3 segundos"""
    print_header("4. PRUEBA DE GRABACIÓN")
    
    output_file = Path.home() / "Desktop" / "test_recording.mp4"
    
    print(f"\n🎬 Intentando grabar 3 segundos de pantalla...")
    print(f"   Archivo de salida: {output_file}")
    
    # Comando básico de ffmpeg para Windows
    cmd = [
        'ffmpeg',
        '-y',  # Sobrescribir sin preguntar
        '-f', 'gdigrab',
        '-framerate', '30',
        '-draw_mouse', '1',  # Capturar cursor
        '-i', 'desktop',
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
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0 and output_file.exists():
            size = output_file.stat().st_size
            print(f"\n✅ ¡Grabación exitosa!")
            print(f"   Archivo creado: {output_file}")
            print(f"   Tamaño: {size / 1024:.1f} KB")
            print(f"\n💡 El video se guardó en el Escritorio")
            print(f"   Puedes abrirlo con cualquier reproductor de video")
            return True
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"\n❌ La grabación falló")
            print(f"\n📋 Error de ffmpeg:")
            # Mostrar últimas líneas del error
            error_lines = [l for l in stderr.split('\n') if l.strip()][-20:]
            print("   " + "\n   ".join(error_lines))
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ Timeout - ffmpeg no respondió en 10 segundos")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_audio():
    """Prueba grabación con audio"""
    print_header("5. PRUEBA DE GRABACIÓN CON AUDIO")
    
    output_file = Path.home() / "Desktop" / "test_recording_audio.mp4"
    
    print(f"\n🎬 Intentando grabar 3 segundos con audio...")
    print(f"   Archivo de salida: {output_file}")
    print(f"\n⚠️  Nota: En Windows, la captura de audio del sistema requiere")
    print(f"   configuración adicional o software como 'Stereo Mix'")
    
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'gdigrab',
        '-framerate', '30',
        '-draw_mouse', '1',
        '-i', 'desktop',
        '-f', 'dshow',
        '-i', 'audio="Mezcla estéreo"',  # Nombre común del dispositivo
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
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0 and output_file.exists():
            print(f"\n✅ ¡Grabación con audio exitosa!")
            print(f"   Archivo: {output_file}")
            return True
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"\n⚠️  La grabación con audio falló")
            print(f"   Esto es común en Windows si:")
            print(f"   • No hay 'Mezcla estéreo' (Stereo Mix) habilitado")
            print(f"   • El dispositivo de audio tiene un nombre diferente")
            print(f"   • No hay micrófono conectado")
            print(f"\n   💡 Puedes grabar sin audio usando audio=False")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def check_stereo_mix():
    """Proporciona instrucciones para habilitar Stereo Mix"""
    print_header("6. CONFIGURAR CAPTURA DE AUDIO DEL SISTEMA")
    
    print("\n🔊 Para capturar audio del sistema en Windows:")
    print("\n   OPCIÓN 1: Habilitar 'Mezcla estéreo' (Stereo Mix)")
    print("   1. Click derecho en el icono de volumen (barra de tareas)")
    print("   2. Selecciona 'Sonidos' o 'Configuración de sonido'")
    print("   3. Ve a la pestaña 'Grabación'")
    print("   4. Click derecho en el área vacía → 'Mostrar dispositivos deshabilitados'")
    print("   5. Busca 'Mezcla estéreo' o 'Stereo Mix'")
    print("   6. Click derecho → 'Habilitar'")
    print("   7. Click derecho → 'Establecer como dispositivo predeterminado'")
    
    print("\n   OPCIÓN 2: Usar solo captura de video")
    print("   • Configura la grabación con audio=False")
    print("   • Es más confiable y consume menos recursos")
    
    print("\n   OPCIÓN 3: Software de terceros")
    print("   • VB-Audio Virtual Cable")
    print("   • Voicemeeter")
    
    return True


def main():
    print("\n" + "🔍 DIAGNÓSTICO DE GRABACIÓN DE PANTALLA EN WINDOWS")
    
    # 1. Verificar Windows
    if not check_windows():
        return
    
    # 2. Verificar ffmpeg
    if not check_ffmpeg():
        return
    
    # 3. Info de gdigrab
    list_gdigrab_info()
    
    # 4. Listar dispositivos de audio
    list_audio_devices()
    
    # 5. Prueba básica
    input("\n⏸️  Presiona Enter para hacer una prueba de grabación...")
    basic_ok = test_basic_recording()
    
    # 6. Prueba con audio
    if basic_ok:
        print("\n💡 La grabación básica funciona. ¿Quieres probar con audio?")
        print("   (Puede fallar si no está configurado Stereo Mix)")
        response = input("   Probar con audio? (s/n): ")
        if response.lower() in ['s', 'y', 'si', 'yes']:
            test_with_audio()
    
    # 7. Info sobre Stereo Mix
    check_stereo_mix()
    
    # Resumen final
    print_header("RESUMEN Y RECOMENDACIONES")
    
    if basic_ok:
        print("\n✅ La grabación de pantalla funciona correctamente")
        print("\n💡 Recomendaciones para Windows:")
        print("   • Usa audio=False si no necesitas audio del sistema")
        print("   • preset='ultrafast' o 'veryfast' para mejor rendimiento")
        print("   • crf=23 es un buen balance calidad/tamaño (18=mejor, 28=menor)")
        print("   • La captura de cursor está habilitada por defecto")
    else:
        print("\n❌ La grabación de pantalla tiene problemas")
        print("\n🔧 Posibles soluciones:")
        print("   1. Verifica que ffmpeg esté en el PATH del sistema")
        print("   2. Reinicia la aplicación/terminal después de instalar ffmpeg")
        print("   3. Ejecuta la aplicación como Administrador si hay permisos")
        print("   4. Revisa los errores de ffmpeg mostrados arriba")
        print("   5. Verifica que no haya antivirus bloqueando ffmpeg")
    
    print("\n📝 Configuración recomendada para Windows:")
    print("""
    recorder = ScreenRecorder(Path("./grabaciones"))
    recorder.configure(
        fps=30,              # 30 fps para la mayoría de casos
        preset='ultrafast',  # Mejor rendimiento
        crf=23,             # Balance calidad/tamaño
        audio=False,        # Sin audio (más confiable)
        capture_cursor=True  # Capturar cursor
    )
    """)
    
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
