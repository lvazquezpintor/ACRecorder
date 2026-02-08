"""
ACC Race Recorder - Servicio de grabación automática para Assetto Corsa Competizione
Graba la pantalla y telemetría sincronizada durante las carreras
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
import psutil

class ACCRecorderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ACC Race Recorder")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Variables de estado
        self.is_monitoring = False
        self.is_recording = False
        self.monitor_thread = None
        self.recording_thread = None
        self.telemetry_thread = None
        self.ffmpeg_process = None
        self.recording_start_time = None
        self.output_dir = Path.home() / "ACC_Recordings"
        self.current_session_dir = None
        self.telemetry_data = []
        
        # Crear directorio de salida
        self.output_dir.mkdir(exist_ok=True)
        
        # Configurar la interfaz
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="ACC Race Recorder", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Estado del servicio
        status_frame = ttk.LabelFrame(main_frame, text="Estado", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Servicio detenido", 
                                      font=('Arial', 10))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.indicator = tk.Canvas(status_frame, width=20, height=20)
        self.indicator.grid(row=0, column=1, padx=10)
        self.indicator.create_oval(2, 2, 18, 18, fill="red", tags="indicator")
        
        # Botones de control
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Iniciar Servicio", 
                                       command=self.start_monitoring, width=20)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Detener Servicio", 
                                      command=self.stop_monitoring, width=20, 
                                      state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Log de eventos
        log_frame = ttk.LabelFrame(main_frame, text="Log de Eventos", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, 
                                                  state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Información de ruta de salida
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        ttk.Label(info_frame, text=f"Grabaciones en: {self.output_dir}", 
                 font=('Arial', 8)).grid(row=0, column=0)
        
    def log(self, message):
        """Añade un mensaje al log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def update_status(self, status_text, is_active):
        """Actualiza el estado visual del servicio"""
        self.status_label.config(text=status_text)
        color = "green" if is_active else "red"
        self.indicator.itemconfig("indicator", fill=color)
        
    def start_monitoring(self):
        """Inicia el servicio de monitoreo de ACC"""
        self.is_monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Servicio activo - Esperando ACC...", True)
        self.log("✓ Servicio iniciado - Monitoreando Assetto Corsa Competizione")
        
        # Iniciar thread de monitoreo
        self.monitor_thread = threading.Thread(target=self.monitor_acc, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Detiene el servicio de monitoreo"""
        self.is_monitoring = False
        
        # Detener grabación si está activa
        if self.is_recording:
            self.stop_recording()
            
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Servicio detenido", False)
        self.log("✗ Servicio detenido")
        
    def monitor_acc(self):
        """Monitorea si ACC está en ejecución y si hay una carrera activa"""
        from acc_telemetry import ACCTelemetry
        
        acc_telemetry = ACCTelemetry()
        self.log("Monitoreando proceso de ACC...")
        
        while self.is_monitoring:
            try:
                # Verificar si ACC está corriendo
                acc_running = self.is_acc_running()
                
                if acc_running and not self.is_recording:
                    # Verificar si hay una sesión activa
                    if acc_telemetry.connect():
                        session_data = acc_telemetry.get_session_info()
                        
                        if session_data and session_data.get('session_type') in ['Race', 'Practice', 'Qualifying']:
                            self.log(f"⚑ Sesión detectada: {session_data.get('session_type')}")
                            self.start_recording()
                
                elif not acc_running and self.is_recording:
                    self.log("ACC cerrado - Deteniendo grabación")
                    self.stop_recording()
                    
                elif self.is_recording:
                    # Verificar si la sesión sigue activa
                    if acc_telemetry.connect():
                        session_data = acc_telemetry.get_session_info()
                        if not session_data or session_data.get('status') == 'Finished':
                            self.log("⚑ Carrera finalizada")
                            self.stop_recording()
                
            except Exception as e:
                self.log(f"Error en monitoreo: {str(e)}")
            
            time.sleep(2)  # Verificar cada 2 segundos
            
        acc_telemetry.disconnect()
        
    def is_acc_running(self):
        """Verifica si Assetto Corsa Competizione está en ejecución"""
        for proc in psutil.process_iter(['name']):
            try:
                if 'AC2' in proc.info['name'] or 'Assetto' in proc.info['name']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
        
    def start_recording(self):
        """Inicia la grabación de pantalla y telemetría"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.recording_start_time = datetime.now()
        
        # Crear directorio para esta sesión
        session_name = self.recording_start_time.strftime("ACC_%Y%m%d_%H%M%S")
        self.current_session_dir = self.output_dir / session_name
        self.current_session_dir.mkdir(exist_ok=True)
        
        self.update_status("⦿ GRABANDO CARRERA", True)
        self.log(f"🔴 INICIANDO GRABACIÓN: {session_name}")
        
        # Iniciar grabación de pantalla
        self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
        self.recording_thread.start()
        
        # Iniciar captura de telemetría
        self.telemetry_data = []
        self.telemetry_thread = threading.Thread(target=self.record_telemetry, daemon=True)
        self.telemetry_thread.start()
        
    def stop_recording(self):
        """Detiene la grabación de pantalla y telemetría"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.log("⏹ Deteniendo grabación...")
        
        # Detener FFmpeg
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except:
                self.ffmpeg_process.kill()
            self.ffmpeg_process = None
        
        # Esperar a que terminen los threads
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=3)
            
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            self.telemetry_thread.join(timeout=3)
        
        # Guardar datos de telemetría
        if self.telemetry_data and self.current_session_dir:
            telemetry_file = self.current_session_dir / "telemetry.json"
            with open(telemetry_file, 'w', encoding='utf-8') as f:
                json.dump(self.telemetry_data, f, indent=2, ensure_ascii=False)
            self.log(f"✓ Telemetría guardada: {len(self.telemetry_data)} registros")
        
        duration = (datetime.now() - self.recording_start_time).total_seconds()
        self.log(f"✓ Grabación completada ({duration:.0f}s)")
        self.log(f"📁 Archivos guardados en: {self.current_session_dir}")
        
        self.update_status("Servicio activo - Esperando ACC...", True)
        
    def record_screen(self):
        """Graba la pantalla usando FFmpeg"""
        video_file = self.current_session_dir / "race_recording.mp4"
        
        # Comando FFmpeg para Windows (captura DirectShow)
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'gdigrab',  # Captura de pantalla en Windows
            '-framerate', '30',  # 30 FPS
            '-i', 'desktop',  # Capturar todo el escritorio
            '-c:v', 'libx264',  # Codec H.264
            '-preset', 'ultrafast',  # Preset rápido para grabación en tiempo real
            '-crf', '23',  # Calidad (0-51, menor = mejor calidad)
            '-pix_fmt', 'yuv420p',  # Formato de píxeles compatible
            str(video_file)
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.log("🎥 Grabación de pantalla iniciada")
            self.ffmpeg_process.wait()
            
        except FileNotFoundError:
            self.log("❌ ERROR: FFmpeg no encontrado. Instala FFmpeg y añádelo al PATH")
        except Exception as e:
            self.log(f"❌ Error en grabación de pantalla: {str(e)}")
            
    def record_telemetry(self):
        """Captura telemetría cada segundo"""
        from acc_telemetry import ACCTelemetry
        
        acc_telemetry = ACCTelemetry()
        second_counter = 0
        
        self.log("📊 Captura de telemetría iniciada")
        
        while self.is_recording:
            try:
                if acc_telemetry.connect():
                    # Obtener datos de la sesión
                    session_data = acc_telemetry.get_session_info()
                    standings = acc_telemetry.get_standings()
                    player_data = acc_telemetry.get_player_telemetry()
                    
                    # Crear registro para este segundo
                    record = {
                        'second': second_counter,
                        'timestamp': datetime.now().isoformat(),
                        'session': session_data,
                        'standings': standings,
                        'player_telemetry': player_data
                    }
                    
                    self.telemetry_data.append(record)
                    second_counter += 1
                    
            except Exception as e:
                self.log(f"Error en captura de telemetría: {str(e)}")
            
            time.sleep(1)  # Capturar cada segundo
        
        acc_telemetry.disconnect()

def main():
    root = tk.Tk()
    app = ACCRecorderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
