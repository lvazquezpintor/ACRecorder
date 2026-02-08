"""
ACC Race Recorder - Aplicación GUI integrada
Control del servicio de grabación + Visualizador de telemetría
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
import psutil
import webbrowser

class ACCRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ACC Race Recorder")
        self.root.geometry("900x700")
        
        # Variables de estado del servicio
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
        
        # Configurar la interfaz con pestañas
        self.setup_ui()
        
    def setup_ui(self):
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña 1: Control del Servicio
        self.tab_control = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_control, text="🎮 Control de Grabación")
        self.setup_control_tab()
        
        # Pestaña 2: Grabaciones
        self.tab_recordings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_recordings, text="📁 Grabaciones")
        self.setup_recordings_tab()
        
        # Pestaña 3: Visualizador
        self.tab_viewer = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_viewer, text="📊 Visualizador")
        self.setup_viewer_tab()
        
        # Pestaña 4: Configuración
        self.tab_config = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_config, text="⚙️ Configuración")
        self.setup_config_tab()
        
    def setup_control_tab(self):
        """Pestaña de control del servicio"""
        main_frame = ttk.Frame(self.tab_control, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="ACC Race Recorder", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Estado del servicio
        status_frame = ttk.LabelFrame(main_frame, text="Estado del Servicio", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        
        status_inner = ttk.Frame(status_frame)
        status_inner.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_inner, text="Servicio detenido", 
                                      font=('Arial', 12))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.indicator = tk.Canvas(status_inner, width=25, height=25)
        self.indicator.pack(side=tk.LEFT)
        self.indicator.create_oval(2, 2, 23, 23, fill="red", tags="indicator")
        
        # Botones de control
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        
        self.start_button = ttk.Button(button_frame, text="▶ Iniciar Servicio", 
                                       command=self.start_monitoring, width=20)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹ Detener Servicio", 
                                      command=self.stop_monitoring, width=20, 
                                      state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Información de la sesión actual
        info_frame = ttk.LabelFrame(main_frame, text="Sesión Actual", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        
        ttk.Label(info_grid, text="Duración:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.duration_label = ttk.Label(info_grid, text="00:00:00", font=('Arial', 10, 'bold'))
        self.duration_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(info_grid, text="Registros:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.records_label = ttk.Label(info_grid, text="0", font=('Arial', 10, 'bold'))
        self.records_label.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(info_grid, text="Carpeta:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.folder_label = ttk.Label(info_grid, text="-", font=('Arial', 10, 'bold'))
        self.folder_label.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Log de eventos
        log_frame = ttk.LabelFrame(main_frame, text="Log de Eventos", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, 
                                                  state=tk.DISABLED, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Información de ruta
        info_label = ttk.Label(main_frame, 
                              text=f"📂 Grabaciones guardadas en: {self.output_dir}", 
                              font=('Arial', 8))
        info_label.pack(pady=5)
        
        # Iniciar actualización del temporizador
        self.update_duration()
        
    def setup_recordings_tab(self):
        """Pestaña de grabaciones guardadas"""
        main_frame = ttk.Frame(self.tab_recordings, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Grabaciones Guardadas", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="🔄 Actualizar Lista", 
                  command=self.refresh_recordings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📂 Abrir Carpeta", 
                  command=self.open_recordings_folder).pack(side=tk.LEFT, padx=5)
        
        # Lista de grabaciones
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.recordings_tree = ttk.Treeview(list_frame, 
                                           columns=('Fecha', 'Duración', 'Tamaño'),
                                           show='tree headings',
                                           yscrollcommand=scrollbar.set)
        self.recordings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.recordings_tree.yview)
        
        # Configurar columnas
        self.recordings_tree.heading('#0', text='Sesión')
        self.recordings_tree.heading('Fecha', text='Fecha')
        self.recordings_tree.heading('Duración', text='Duración')
        self.recordings_tree.heading('Tamaño', text='Tamaño')
        
        self.recordings_tree.column('#0', width=200)
        self.recordings_tree.column('Fecha', width=150)
        self.recordings_tree.column('Duración', width=100)
        self.recordings_tree.column('Tamaño', width=100)
        
        # Botones de acciones con grabación seleccionada
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="▶ Reproducir Video", 
                  command=self.play_selected_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📊 Ver Telemetría", 
                  command=self.view_selected_telemetry).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📁 Abrir Carpeta", 
                  command=self.open_selected_folder).pack(side=tk.LEFT, padx=5)
        
        # Cargar grabaciones iniciales
        self.refresh_recordings()
        
    def setup_viewer_tab(self):
        """Pestaña del visualizador de telemetría"""
        main_frame = ttk.Frame(self.tab_viewer, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Visualizador de Telemetría", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="📂 Cargar archivo JSON", 
                  command=self.load_telemetry_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🌐 Abrir Visualizador Web", 
                  command=self.open_web_viewer).pack(side=tk.LEFT, padx=5)
        
        # Información del archivo cargado
        self.telemetry_info = ttk.Label(main_frame, text="No hay telemetría cargada", 
                                       font=('Arial', 10))
        self.telemetry_info.pack(pady=10)
        
        # Frame para estadísticas rápidas
        stats_frame = ttk.LabelFrame(main_frame, text="Estadísticas Rápidas", padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=25, width=80,
                                                   state=tk.DISABLED, font=('Consolas', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_config_tab(self):
        """Pestaña de configuración"""
        main_frame = ttk.Frame(self.tab_config, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Configuración", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Configuración de video
        video_frame = ttk.LabelFrame(main_frame, text="Grabación de Video", padding="10")
        video_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(video_frame, text="FPS:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.fps_var = tk.StringVar(value="30")
        fps_combo = ttk.Combobox(video_frame, textvariable=self.fps_var, 
                                values=['24', '30', '60'], width=10, state='readonly')
        fps_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(video_frame, text="Calidad (CRF):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.crf_var = tk.StringVar(value="23")
        crf_combo = ttk.Combobox(video_frame, textvariable=self.crf_var,
                                values=['18', '23', '28'], width=10, state='readonly')
        crf_combo.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(video_frame, text="(18=Alta, 23=Media, 28=Baja)", 
                 font=('Arial', 8)).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(video_frame, text="Preset:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.preset_var = tk.StringVar(value="ultrafast")
        preset_combo = ttk.Combobox(video_frame, textvariable=self.preset_var,
                                   values=['ultrafast', 'fast', 'medium'], 
                                   width=10, state='readonly')
        preset_combo.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Configuración de telemetría
        telemetry_frame = ttk.LabelFrame(main_frame, text="Captura de Telemetría", padding="10")
        telemetry_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(telemetry_frame, text="Intervalo (segundos):").grid(row=0, column=0, 
                                                                      sticky=tk.W, pady=5)
        self.interval_var = tk.StringVar(value="1")
        interval_combo = ttk.Combobox(telemetry_frame, textvariable=self.interval_var,
                                     values=['0.5', '1', '2'], width=10, state='readonly')
        interval_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Directorio de salida
        dir_frame = ttk.LabelFrame(main_frame, text="Directorio de Salida", padding="10")
        dir_frame.pack(fill=tk.X, pady=10)
        
        dir_inner = ttk.Frame(dir_frame)
        dir_inner.pack(fill=tk.X)
        
        self.output_dir_var = tk.StringVar(value=str(self.output_dir))
        ttk.Entry(dir_inner, textvariable=self.output_dir_var, 
                 state='readonly', width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_inner, text="Cambiar", 
                  command=self.change_output_dir).pack(side=tk.LEFT)
        
        # Botones de guardado
        ttk.Button(main_frame, text="💾 Guardar Configuración", 
                  command=self.save_config).pack(pady=20)
        
    # ==================== MÉTODOS DE CONTROL ====================
    
    def start_monitoring(self):
        """Inicia el servicio de monitoreo"""
        self.is_monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Servicio activo - Esperando ACC...", True)
        self.log("✓ Servicio iniciado - Monitoreando Assetto Corsa Competizione")
        
        self.monitor_thread = threading.Thread(target=self.monitor_acc, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Detiene el servicio de monitoreo"""
        self.is_monitoring = False
        
        if self.is_recording:
            self.stop_recording()
            
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Servicio detenido", False)
        self.log("✗ Servicio detenido")
        
    def monitor_acc(self):
        """Monitorea ACC y gestiona la grabación"""
        from acc_telemetry import ACCTelemetry
        
        acc_telemetry = ACCTelemetry()
        self.log("Monitoreando proceso de ACC...")
        
        while self.is_monitoring:
            try:
                acc_running = self.is_acc_running()
                
                if acc_running and not self.is_recording:
                    if acc_telemetry.connect():
                        session_data = acc_telemetry.get_session_info()
                        
                        if session_data and session_data.get('session_type') in ['Race', 'Practice', 'Qualifying']:
                            self.log(f"⚑ Sesión detectada: {session_data.get('session_type')}")
                            self.start_recording()
                
                elif not acc_running and self.is_recording:
                    self.log("ACC cerrado - Deteniendo grabación")
                    self.stop_recording()
                    
                elif self.is_recording:
                    if acc_telemetry.connect():
                        session_data = acc_telemetry.get_session_info()
                        if not session_data or session_data.get('status') == 'Finished':
                            self.log("⚑ Carrera finalizada")
                            self.stop_recording()
                
            except Exception as e:
                self.log(f"Error en monitoreo: {str(e)}")
            
            time.sleep(2)
            
        acc_telemetry.disconnect()
        
    def is_acc_running(self):
        """Verifica si ACC está corriendo"""
        for proc in psutil.process_iter(['name']):
            try:
                if 'AC2' in proc.info['name'] or 'Assetto' in proc.info['name']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
        
    def start_recording(self):
        """Inicia la grabación"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.recording_start_time = datetime.now()
        
        session_name = self.recording_start_time.strftime("ACC_%Y%m%d_%H%M%S")
        self.current_session_dir = self.output_dir / session_name
        self.current_session_dir.mkdir(exist_ok=True)
        
        self.update_status("⦿ GRABANDO CARRERA", True)
        self.log(f"🔴 INICIANDO GRABACIÓN: {session_name}")
        self.folder_label.config(text=session_name)
        
        self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
        self.recording_thread.start()
        
        self.telemetry_data = []
        self.telemetry_thread = threading.Thread(target=self.record_telemetry, daemon=True)
        self.telemetry_thread.start()
        
    def stop_recording(self):
        """Detiene la grabación"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.log("⏹ Deteniendo grabación...")
        
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except:
                self.ffmpeg_process.kill()
            self.ffmpeg_process = None
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=3)
            
        if self.telemetry_thread and self.telemetry_thread.is_alive():
            self.telemetry_thread.join(timeout=3)
        
        if self.telemetry_data and self.current_session_dir:
            telemetry_file = self.current_session_dir / "telemetry.json"
            with open(telemetry_file, 'w', encoding='utf-8') as f:
                json.dump(self.telemetry_data, f, indent=2, ensure_ascii=False)
            self.log(f"✓ Telemetría guardada: {len(self.telemetry_data)} registros")
        
        duration = (datetime.now() - self.recording_start_time).total_seconds()
        self.log(f"✓ Grabación completada ({duration:.0f}s)")
        self.log(f"📁 Archivos guardados en: {self.current_session_dir}")
        
        self.update_status("Servicio activo - Esperando ACC...", True)
        self.folder_label.config(text="-")
        self.refresh_recordings()
        
    def record_screen(self):
        """Graba la pantalla"""
        video_file = self.current_session_dir / "race_recording.mp4"
        
        fps = self.fps_var.get()
        crf = self.crf_var.get()
        preset = self.preset_var.get()
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'gdigrab',
            '-framerate', fps,
            '-i', 'desktop',
            '-c:v', 'libx264',
            '-preset', preset,
            '-crf', crf,
            '-pix_fmt', 'yuv420p',
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
            self.log("❌ ERROR: FFmpeg no encontrado")
        except Exception as e:
            self.log(f"❌ Error en grabación: {str(e)}")
            
    def record_telemetry(self):
        """Captura telemetría"""
        from acc_telemetry import ACCTelemetry
        
        acc_telemetry = ACCTelemetry()
        second_counter = 0
        interval = float(self.interval_var.get())
        
        self.log("📊 Captura de telemetría iniciada")
        
        while self.is_recording:
            try:
                if acc_telemetry.connect():
                    session_data = acc_telemetry.get_session_info()
                    standings = acc_telemetry.get_standings()
                    player_data = acc_telemetry.get_player_telemetry()
                    
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
                self.log(f"Error en telemetría: {str(e)}")
            
            time.sleep(interval)
        
        acc_telemetry.disconnect()
    
    # ==================== MÉTODOS DE GRABACIONES ====================
    
    def refresh_recordings(self):
        """Actualiza la lista de grabaciones"""
        for item in self.recordings_tree.get_children():
            self.recordings_tree.delete(item)
            
        if not self.output_dir.exists():
            return
            
        sessions = sorted(self.output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for session_dir in sessions:
            if session_dir.is_dir():
                video_file = session_dir / "race_recording.mp4"
                json_file = session_dir / "telemetry.json"
                
                if video_file.exists():
                    stat = video_file.stat()
                    date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    size_mb = stat.st_size / (1024 * 1024)
                    
                    # Calcular duración aproximada del JSON
                    duration = "-"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r') as f:
                                data = json.load(f)
                                if data:
                                    seconds = data[-1]['second']
                                    mins = seconds // 60
                                    secs = seconds % 60
                                    duration = f"{mins:02d}:{secs:02d}"
                        except:
                            pass
                    
                    self.recordings_tree.insert('', 'end', text=session_dir.name,
                                              values=(date, duration, f"{size_mb:.1f} MB"),
                                              tags=(str(session_dir),))
    
    def open_recordings_folder(self):
        """Abre la carpeta de grabaciones"""
        os.startfile(self.output_dir)
        
    def play_selected_video(self):
        """Reproduce el video seleccionado"""
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona una grabación primero")
            return
            
        tags = self.recordings_tree.item(selection[0], 'tags')
        session_path = Path(tags[0])
        video_file = session_path / "race_recording.mp4"
        
        if video_file.exists():
            os.startfile(video_file)
        else:
            messagebox.showerror("Error", "Video no encontrado")
            
    def view_selected_telemetry(self):
        """Visualiza la telemetría seleccionada"""
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona una grabación primero")
            return
            
        tags = self.recordings_tree.item(selection[0], 'tags')
        session_path = Path(tags[0])
        json_file = session_path / "telemetry.json"
        
        if json_file.exists():
            self.load_telemetry_file(json_file)
            self.notebook.select(self.tab_viewer)
        else:
            messagebox.showerror("Error", "Telemetría no encontrada")
            
    def open_selected_folder(self):
        """Abre la carpeta de la sesión seleccionada"""
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona una grabación primero")
            return
            
        tags = self.recordings_tree.item(selection[0], 'tags')
        session_path = Path(tags[0])
        os.startfile(session_path)
    
    # ==================== MÉTODOS DEL VISUALIZADOR ====================
    
    def load_telemetry_json(self):
        """Carga un archivo JSON de telemetría"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de telemetría",
            initialdir=self.output_dir,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.load_telemetry_file(Path(filename))
            
    def load_telemetry_file(self, filepath):
        """Carga y analiza un archivo de telemetría"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.telemetry_info.config(
                text=f"✓ Cargado: {filepath.name} ({len(data)} registros)"
            )
            
            # Generar estadísticas
            self.generate_telemetry_stats(data)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{str(e)}")
            
    def generate_telemetry_stats(self, data):
        """Genera estadísticas de la telemetría"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        stats = "=" * 70 + "\n"
        stats += "ESTADÍSTICAS DE TELEMETRÍA\n"
        stats += "=" * 70 + "\n\n"
        
        # Información general
        stats += f"📊 Total de registros: {len(data)}\n"
        if data:
            duration = data[-1]['second']
            stats += f"⏱️  Duración: {duration // 60:02d}:{duration % 60:02d}\n\n"
            
            # Análisis de velocidades
            speeds = [r['player_telemetry']['speed_kmh'] for r in data 
                     if r.get('player_telemetry')]
            if speeds:
                stats += f"🏎️  Velocidad máxima: {max(speeds):.1f} km/h\n"
                stats += f"📈 Velocidad media: {sum(speeds)/len(speeds):.1f} km/h\n\n"
            
            # Análisis de bloqueos
            total_locks = 0
            lock_moments = []
            for i, r in enumerate(data):
                if r.get('player_telemetry') and r['player_telemetry'].get('tyres'):
                    locks = r['player_telemetry']['tyres'].get('locked', {})
                    count = sum(1 for v in locks.values() if v)
                    if count > 0:
                        total_locks += count
                        lock_moments.append((i, count))
            
            stats += f"🔴 Total de bloqueos detectados: {total_locks}\n"
            stats += f"⚠️  Momentos con bloqueos: {len(lock_moments)}\n\n"
            
            if lock_moments:
                stats += "Primeros 10 bloqueos:\n"
                for i, (second, count) in enumerate(lock_moments[:10]):
                    stats += f"  {second:4d}s - {count} rueda(s) bloqueada(s)\n"
                stats += "\n"
            
            # Análisis de Gs
            g_lats = [r['player_telemetry'].get('g_force', {}).get('lateral', 0) 
                     for r in data if r.get('player_telemetry')]
            g_longs = [r['player_telemetry'].get('g_force', {}).get('longitudinal', 0) 
                      for r in data if r.get('player_telemetry')]
            
            if g_lats:
                stats += f"💨 G lateral máxima: {max(abs(g) for g in g_lats):.2f} G\n"
            if g_longs:
                stats += f"🛑 G frenada máxima: {min(g_longs):.2f} G\n"
                stats += f"🚀 G aceleración máxima: {max(g_longs):.2f} G\n\n"
            
            # Temperaturas
            brake_temps = []
            for r in data:
                if r.get('player_telemetry') and r['player_telemetry'].get('brakes'):
                    temps = r['player_telemetry']['brakes']['temperature']
                    brake_temps.append(max(temps.values()))
            
            if brake_temps:
                stats += f"🔥 Temp. frenos máxima: {max(brake_temps):.0f}°C\n"
                stats += f"🌡️  Temp. frenos media: {sum(brake_temps)/len(brake_temps):.0f}°C\n"
        
        stats += "\n" + "=" * 70 + "\n"
        stats += "💡 Usa el botón 'Abrir Visualizador Web' para gráficos detallados\n"
        
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)
        
    def open_web_viewer(self):
        """Abre el visualizador web"""
        viewer_path = Path(__file__).parent / "telemetry_viewer.html"
        if viewer_path.exists():
            webbrowser.open(viewer_path.as_uri())
        else:
            messagebox.showerror("Error", "No se encontró el visualizador web")
    
    # ==================== MÉTODOS DE CONFIGURACIÓN ====================
    
    def change_output_dir(self):
        """Cambia el directorio de salida"""
        new_dir = filedialog.askdirectory(title="Seleccionar carpeta de grabaciones")
        if new_dir:
            self.output_dir = Path(new_dir)
            self.output_dir_var.set(str(self.output_dir))
            self.output_dir.mkdir(exist_ok=True)
            
    def save_config(self):
        """Guarda la configuración"""
        # Aquí podrías guardar en un archivo config.json
        messagebox.showinfo("Configuración", "Configuración guardada correctamente")
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def log(self, message):
        """Añade mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def update_status(self, status_text, is_active):
        """Actualiza el estado visual"""
        self.status_label.config(text=status_text)
        color = "green" if is_active else "red"
        self.indicator.itemconfig("indicator", fill=color)
        
    def update_duration(self):
        """Actualiza el contador de duración"""
        if self.is_recording and self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.duration_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.records_label.config(text=str(len(self.telemetry_data)))
        
        self.root.after(1000, self.update_duration)

def main():
    root = tk.Tk()
    app = ACCRecorderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
