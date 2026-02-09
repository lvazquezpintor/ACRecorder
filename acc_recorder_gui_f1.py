"""
ACC Race Recorder - F1 Inspired Modern GUI
Diseño inspirado en la Fórmula 1 con estética racing profesional
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

class ModernF1GUI:
    """GUI moderna inspirada en el diseño de la Fórmula 1"""
    
    # Paleta de colores F1 Racing
    COLORS = {
        'bg_dark': '#0A0A0A',           # Negro carbono
        'bg_medium': '#1A1A1A',         # Gris oscuro
        'bg_light': '#2A2A2A',          # Gris medio
        'accent_red': '#E10600',        # Rojo Ferrari/F1
        'accent_cyan': '#00D9FF',       # Cyan tecnológico
        'accent_green': '#00FF41',      # Verde neón
        'accent_orange': '#FF8700',     # Naranja McLaren
        'text_white': '#FFFFFF',        # Blanco puro
        'text_gray': '#999999',         # Gris texto
        'warning': '#FFD700',           # Amarillo bandera
        'danger': '#FF1744',            # Rojo peligro
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("ACC RACE RECORDER")
        self.root.geometry("1100x750")
        self.root.configure(bg=self.COLORS['bg_dark'])
        
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
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Configurar estilo moderno
        self.setup_modern_style()
        
        # Crear interfaz
        self.setup_ui()
        
    def setup_modern_style(self):
        """Configura el estilo visual moderno inspirado en F1"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar Notebook (pestañas)
        style.configure('TNotebook', 
                       background=self.COLORS['bg_dark'],
                       borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=self.COLORS['bg_medium'],
                       foreground=self.COLORS['text_gray'],
                       padding=[20, 10],
                       font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.COLORS['bg_light'])],
                 foreground=[('selected', self.COLORS['accent_red'])])
        
        # Frames
        style.configure('Dark.TFrame', background=self.COLORS['bg_dark'])
        style.configure('Medium.TFrame', background=self.COLORS['bg_medium'])
        style.configure('Light.TFrame', background=self.COLORS['bg_light'])
        
        # Labels
        style.configure('Title.TLabel',
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['text_white'],
                       font=('Arial', 24, 'bold'))
        style.configure('Header.TLabel',
                       background=self.COLORS['bg_medium'],
                       foreground=self.COLORS['accent_red'],
                       font=('Arial', 14, 'bold'))
        style.configure('Normal.TLabel',
                       background=self.COLORS['bg_medium'],
                       foreground=self.COLORS['text_white'],
                       font=('Arial', 10))
        style.configure('Status.TLabel',
                       background=self.COLORS['bg_light'],
                       foreground=self.COLORS['text_white'],
                       font=('Arial', 12, 'bold'))
        
        # Botones
        style.configure('Accent.TButton',
                       background=self.COLORS['accent_red'],
                       foreground=self.COLORS['text_white'],
                       borderwidth=0,
                       font=('Arial', 11, 'bold'),
                       padding=[20, 10])
        style.map('Accent.TButton',
                 background=[('active', '#C10500')])
        
        style.configure('Secondary.TButton',
                       background=self.COLORS['bg_light'],
                       foreground=self.COLORS['text_white'],
                       borderwidth=1,
                       font=('Arial', 10, 'bold'),
                       padding=[15, 8])
        style.map('Secondary.TButton',
                 background=[('active', self.COLORS['bg_medium'])])
        
        # LabelFrame
        style.configure('Modern.TLabelframe',
                       background=self.COLORS['bg_medium'],
                       borderwidth=2,
                       relief='flat')
        style.configure('Modern.TLabelframe.Label',
                       background=self.COLORS['bg_medium'],
                       foreground=self.COLORS['accent_red'],
                       font=('Arial', 11, 'bold'))
        
    def setup_ui(self):
        """Crea la interfaz principal"""
        # Header con título estilo F1
        header = tk.Frame(self.root, bg=self.COLORS['bg_dark'], height=80)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        
        # Línea roja superior (característica F1)
        top_line = tk.Frame(header, bg=self.COLORS['accent_red'], height=3)
        top_line.pack(fill=tk.X)
        
        # Título principal
        title_frame = tk.Frame(header, bg=self.COLORS['bg_dark'])
        title_frame.pack(expand=True, fill=tk.BOTH)
        
        title = tk.Label(title_frame,
                        text="ACC RACE RECORDER",
                        bg=self.COLORS['bg_dark'],
                        fg=self.COLORS['text_white'],
                        font=('Arial', 28, 'bold'),
                        anchor='w')
        title.pack(side=tk.LEFT, padx=30, pady=10)
        
        # Subtítulo
        subtitle = tk.Label(title_frame,
                           text="TELEMETRY & RECORDING SYSTEM",
                           bg=self.COLORS['bg_dark'],
                           fg=self.COLORS['text_gray'],
                           font=('Arial', 10),
                           anchor='w')
        subtitle.pack(side=tk.LEFT, padx=10)
        
        # Línea divisoria
        divider = tk.Frame(self.root, bg=self.COLORS['accent_red'], height=2)
        divider.pack(fill=tk.X)
        
        # Notebook con pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Crear pestañas
        self.tab_control = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(self.tab_control, text="  🏁 CONTROL  ")
        self.setup_control_tab()
        
        self.tab_recordings = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(self.tab_recordings, text="  📹 SESSIONS  ")
        self.setup_recordings_tab()
        
        self.tab_viewer = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(self.tab_viewer, text="  📊 ANALYTICS  ")
        self.setup_viewer_tab()
        
        self.tab_config = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(self.tab_config, text="  ⚙️ SETTINGS  ")
        self.setup_config_tab()
        
    def setup_control_tab(self):
        """Pestaña de control con diseño F1"""
        # Contenedor principal
        main = tk.Frame(self.tab_control, bg=self.COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Panel de estado (HUD style)
        status_panel = tk.Frame(main, bg=self.COLORS['bg_medium'], 
                               highlightbackground=self.COLORS['accent_red'],
                               highlightthickness=2)
        status_panel.pack(fill=tk.X, pady=(0, 20))
        
        # Barra superior del panel
        status_header = tk.Frame(status_panel, bg=self.COLORS['accent_red'], height=40)
        status_header.pack(fill=tk.X)
        status_header.pack_propagate(False)
        
        status_title = tk.Label(status_header,
                               text="SYSTEM STATUS",
                               bg=self.COLORS['accent_red'],
                               fg=self.COLORS['text_white'],
                               font=('Arial', 12, 'bold'))
        status_title.pack(side=tk.LEFT, padx=15, pady=8)
        
        # Contenido del panel
        status_content = tk.Frame(status_panel, bg=self.COLORS['bg_medium'])
        status_content.pack(fill=tk.X, padx=20, pady=20)
        
        # Indicador y texto de estado
        indicator_frame = tk.Frame(status_content, bg=self.COLORS['bg_medium'])
        indicator_frame.pack(side=tk.LEFT)
        
        self.status_indicator = tk.Canvas(indicator_frame, 
                                         width=30, height=30,
                                         bg=self.COLORS['bg_medium'],
                                         highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 15))
        self.status_indicator.create_oval(5, 5, 25, 25, 
                                         fill=self.COLORS['danger'],
                                         outline=self.COLORS['text_white'],
                                         width=2,
                                         tags="indicator")
        
        self.status_text = tk.Label(status_content,
                                   text="OFFLINE",
                                   bg=self.COLORS['bg_medium'],
                                   fg=self.COLORS['text_gray'],
                                   font=('Arial', 16, 'bold'))
        self.status_text.pack(side=tk.LEFT)
        
        # Botones de control
        button_panel = tk.Frame(main, bg=self.COLORS['bg_dark'])
        button_panel.pack(fill=tk.X, pady=20)
        
        # Botón START (grande y destacado)
        self.start_btn = tk.Button(button_panel,
                                   text="▶ START MONITORING",
                                   bg=self.COLORS['accent_green'],
                                   fg=self.COLORS['bg_dark'],
                                   font=('Arial', 14, 'bold'),
                                   relief=tk.FLAT,
                                   cursor='hand2',
                                   command=self.start_monitoring,
                                   padx=40, pady=15)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        # Botón STOP
        self.stop_btn = tk.Button(button_panel,
                                  text="⏹ STOP",
                                  bg=self.COLORS['bg_light'],
                                  fg=self.COLORS['text_gray'],
                                  font=('Arial', 14, 'bold'),
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  state=tk.DISABLED,
                                  command=self.stop_monitoring,
                                  padx=30, pady=15)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Panel de información de sesión
        info_panel = tk.Frame(main, bg=self.COLORS['bg_medium'],
                             highlightbackground=self.COLORS['accent_cyan'],
                             highlightthickness=2)
        info_panel.pack(fill=tk.X, pady=20)
        
        # Header del panel info
        info_header = tk.Frame(info_panel, bg=self.COLORS['accent_cyan'], height=35)
        info_header.pack(fill=tk.X)
        info_header.pack_propagate(False)
        
        info_title = tk.Label(info_header,
                             text="SESSION DATA",
                             bg=self.COLORS['accent_cyan'],
                             fg=self.COLORS['bg_dark'],
                             font=('Arial', 11, 'bold'))
        info_title.pack(side=tk.LEFT, padx=15, pady=6)
        
        # Grid de datos
        data_grid = tk.Frame(info_panel, bg=self.COLORS['bg_medium'])
        data_grid.pack(fill=tk.X, padx=20, pady=15)
        
        # Crear cards de datos estilo F1
        self.create_data_card(data_grid, "DURATION", "00:00:00", 0, 0)
        self.create_data_card(data_grid, "RECORDS", "0", 0, 1)
        self.create_data_card(data_grid, "SESSION", "—", 1, 0, colspan=2)
        
        # Log de eventos (estilo terminal F1)
        log_panel = tk.Frame(main, bg=self.COLORS['bg_medium'],
                            highlightbackground=self.COLORS['accent_orange'],
                            highlightthickness=2)
        log_panel.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Header del log
        log_header = tk.Frame(log_panel, bg=self.COLORS['accent_orange'], height=35)
        log_header.pack(fill=tk.X)
        log_header.pack_propagate(False)
        
        log_title = tk.Label(log_header,
                            text="EVENT LOG",
                            bg=self.COLORS['accent_orange'],
                            fg=self.COLORS['bg_dark'],
                            font=('Arial', 11, 'bold'))
        log_title.pack(side=tk.LEFT, padx=15, pady=6)
        
        # Área de log
        log_container = tk.Frame(log_panel, bg=self.COLORS['bg_dark'])
        log_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.log_text = scrolledtext.ScrolledText(log_container,
                                                  bg=self.COLORS['bg_dark'],
                                                  fg=self.COLORS['accent_green'],
                                                  font=('Consolas', 9),
                                                  insertbackground=self.COLORS['accent_red'],
                                                  relief=tk.FLAT,
                                                  state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Footer con ruta
        footer = tk.Label(main,
                         text=f"📁 OUTPUT: {self.output_dir}",
                         bg=self.COLORS['bg_dark'],
                         fg=self.COLORS['text_gray'],
                         font=('Arial', 8))
        footer.pack(pady=(10, 0))
        
        # Iniciar actualización
        self.update_duration()
        
    def create_data_card(self, parent, label, value, row, col, colspan=1):
        """Crea una tarjeta de datos estilo F1"""
        card = tk.Frame(parent, bg=self.COLORS['bg_light'],
                       highlightbackground=self.COLORS['text_gray'],
                       highlightthickness=1)
        card.grid(row=row, column=col, columnspan=colspan, 
                 sticky='ew', padx=5, pady=5)
        
        # Label
        lbl = tk.Label(card,
                      text=label,
                      bg=self.COLORS['bg_light'],
                      fg=self.COLORS['text_gray'],
                      font=('Arial', 8, 'bold'))
        lbl.pack(anchor='w', padx=10, pady=(8, 2))
        
        # Valor
        val = tk.Label(card,
                      text=value,
                      bg=self.COLORS['bg_light'],
                      fg=self.COLORS['accent_red'],
                      font=('Arial', 16, 'bold'))
        val.pack(anchor='w', padx=10, pady=(0, 8))
        
        # Guardar referencias
        if label == "DURATION":
            self.duration_label = val
        elif label == "RECORDS":
            self.records_label = val
        elif label == "SESSION":
            self.session_label = val
            
        parent.columnconfigure(col, weight=1)
        
    def setup_recordings_tab(self):
        """Pestaña de grabaciones"""
        main = tk.Frame(self.tab_recordings, bg=self.COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Label(main,
                         text="RECORDED SESSIONS",
                         bg=self.COLORS['bg_dark'],
                         fg=self.COLORS['text_white'],
                         font=('Arial', 18, 'bold'))
        header.pack(pady=(0, 20))
        
        # Botones de acción
        btn_frame = tk.Frame(main, bg=self.COLORS['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame, text="🔄 REFRESH",
                 bg=self.COLORS['bg_light'],
                 fg=self.COLORS['text_white'],
                 font=('Arial', 10, 'bold'),
                 relief=tk.FLAT,
                 cursor='hand2',
                 command=self.refresh_recordings,
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📂 OPEN FOLDER",
                 bg=self.COLORS['bg_light'],
                 fg=self.COLORS['text_white'],
                 font=('Arial', 10, 'bold'),
                 relief=tk.FLAT,
                 cursor='hand2',
                 command=self.open_recordings_folder,
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Lista de grabaciones
        list_container = tk.Frame(main, bg=self.COLORS['bg_medium'],
                                 highlightbackground=self.COLORS['accent_red'],
                                 highlightthickness=2)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar y Treeview
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        style = ttk.Style()
        style.configure("Treeview",
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['text_white'],
                       fieldbackground=self.COLORS['bg_dark'],
                       font=('Arial', 9))
        style.configure("Treeview.Heading",
                       background=self.COLORS['accent_red'],
                       foreground=self.COLORS['text_white'],
                       font=('Arial', 10, 'bold'))
        style.map('Treeview',
                 background=[('selected', self.COLORS['accent_red'])])
        
        self.recordings_tree = ttk.Treeview(list_container,
                                           columns=('Date', 'Duration', 'Size'),
                                           show='tree headings',
                                           yscrollcommand=scrollbar.set)
        self.recordings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.config(command=self.recordings_tree.yview)
        
        self.recordings_tree.heading('#0', text='SESSION')
        self.recordings_tree.heading('Date', text='DATE')
        self.recordings_tree.heading('Duration', text='DURATION')
        self.recordings_tree.heading('Size', text='SIZE')
        
        self.recordings_tree.column('#0', width=250)
        self.recordings_tree.column('Date', width=180)
        self.recordings_tree.column('Duration', width=100)
        self.recordings_tree.column('Size', width=100)
        
        # Botones de acción con selección
        action_frame = tk.Frame(main, bg=self.COLORS['bg_dark'])
        action_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Button(action_frame, text="▶ PLAY VIDEO",
                 bg=self.COLORS['accent_green'],
                 fg=self.COLORS['bg_dark'],
                 font=('Arial', 10, 'bold'),
                 relief=tk.FLAT,
                 cursor='hand2',
                 command=self.play_selected_video,
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(action_frame, text="📊 VIEW DATA",
                 bg=self.COLORS['accent_cyan'],
                 fg=self.COLORS['bg_dark'],
                 font=('Arial', 10, 'bold'),
                 relief=tk.FLAT,
                 cursor='hand2',
                 command=self.view_selected_telemetry,
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        self.refresh_recordings()
        
    def setup_viewer_tab(self):
        """Pestaña del visualizador"""
        main = tk.Frame(self.tab_viewer, bg=self.COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = tk.Label(main,
                         text="TELEMETRY ANALYTICS",
                         bg=self.COLORS['bg_dark'],
                         fg=self.COLORS['text_white'],
                         font=('Arial', 18, 'bold'))
        header.pack(pady=(0, 20))
        
        # Botones
        btn_frame = tk.Frame(main, bg=self.COLORS['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame, text="📂 LOAD JSON",
                 bg=self.COLORS['accent_red'],
                 fg=self.COLORS['text_white'],
                 font=('Arial', 10, 'bold'),
                 relief=tk.FLAT,
                 cursor='hand2',
                 command=self.load_telemetry_json,
                 padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🌐 WEB VIEWER",
                 bg=self.COLORS['accent_cyan'],
                 fg=self.COLORS['bg_dark'],
                 font=('Arial', 10, 'bold'),
                 relief=tk.FLAT,
                 cursor='hand2',
                 command=self.open_web_viewer,
                 padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        
        # Info
        self.telemetry_info = tk.Label(main,
                                      text="No telemetry loaded",
                                      bg=self.COLORS['bg_dark'],
                                      fg=self.COLORS['text_gray'],
                                      font=('Arial', 10))
        self.telemetry_info.pack(pady=10)
        
        # Stats panel
        stats_panel = tk.Frame(main, bg=self.COLORS['bg_medium'],
                              highlightbackground=self.COLORS['accent_orange'],
                              highlightthickness=2)
        stats_panel.pack(fill=tk.BOTH, expand=True)
        
        # Header
        stats_header = tk.Frame(stats_panel, bg=self.COLORS['accent_orange'], height=35)
        stats_header.pack(fill=tk.X)
        stats_header.pack_propagate(False)
        
        stats_title = tk.Label(stats_header,
                              text="QUICK STATS",
                              bg=self.COLORS['accent_orange'],
                              fg=self.COLORS['bg_dark'],
                              font=('Arial', 11, 'bold'))
        stats_title.pack(side=tk.LEFT, padx=15, pady=6)
        
        # Stats text
        stats_container = tk.Frame(stats_panel, bg=self.COLORS['bg_dark'])
        stats_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.stats_text = scrolledtext.ScrolledText(stats_container,
                                                   bg=self.COLORS['bg_dark'],
                                                   fg=self.COLORS['text_white'],
                                                   font=('Consolas', 9),
                                                   relief=tk.FLAT,
                                                   state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_config_tab(self):
        """Pestaña de configuración"""
        main = tk.Frame(self.tab_config, bg=self.COLORS['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = tk.Label(main,
                         text="SYSTEM SETTINGS",
                         bg=self.COLORS['bg_dark'],
                         fg=self.COLORS['text_white'],
                         font=('Arial', 18, 'bold'))
        header.pack(pady=(0, 20))
        
        # Video settings
        video_panel = tk.Frame(main, bg=self.COLORS['bg_medium'],
                              highlightbackground=self.COLORS['accent_red'],
                              highlightthickness=2)
        video_panel.pack(fill=tk.X, pady=10)
        
        video_header = tk.Frame(video_panel, bg=self.COLORS['accent_red'], height=35)
        video_header.pack(fill=tk.X)
        video_header.pack_propagate(False)
        
        tk.Label(video_header, text="VIDEO RECORDING",
                bg=self.COLORS['accent_red'],
                fg=self.COLORS['text_white'],
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=15, pady=6)
        
        video_content = tk.Frame(video_panel, bg=self.COLORS['bg_medium'])
        video_content.pack(fill=tk.X, padx=20, pady=15)
        
        # FPS
        self.create_config_row(video_content, "FPS:", ['24', '30', '60'], '30', 0)
        self.create_config_row(video_content, "Quality (CRF):", ['18', '23', '28'], '23', 1)
        self.create_config_row(video_content, "Preset:", ['ultrafast', 'fast', 'medium'], 'ultrafast', 2)
        
        # Telemetry settings
        telem_panel = tk.Frame(main, bg=self.COLORS['bg_medium'],
                              highlightbackground=self.COLORS['accent_cyan'],
                              highlightthickness=2)
        telem_panel.pack(fill=tk.X, pady=10)
        
        telem_header = tk.Frame(telem_panel, bg=self.COLORS['accent_cyan'], height=35)
        telem_header.pack(fill=tk.X)
        telem_header.pack_propagate(False)
        
        tk.Label(telem_header, text="TELEMETRY CAPTURE",
                bg=self.COLORS['accent_cyan'],
                fg=self.COLORS['bg_dark'],
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=15, pady=6)
        
        telem_content = tk.Frame(telem_panel, bg=self.COLORS['bg_medium'])
        telem_content.pack(fill=tk.X, padx=20, pady=15)
        
        self.create_config_row(telem_content, "Interval (sec):", ['0.5', '1', '2'], '1', 0)
        
        # Save button
        tk.Button(main, text="💾 SAVE CONFIGURATION",
                 bg=self.COLORS['accent_green'],
                 fg=self.COLORS['bg_dark'],
                 font=('Arial', 12, 'bold'),
                 relief=tk.FLAT,
                 cursor='hand2',
                 command=self.save_config,
                 padx=30, pady=12).pack(pady=30)
        
    def create_config_row(self, parent, label, values, default, row):
        """Crea una fila de configuración"""
        frame = tk.Frame(parent, bg=self.COLORS['bg_medium'])
        frame.pack(fill=tk.X, pady=8)
        
        tk.Label(frame, text=label,
                bg=self.COLORS['bg_medium'],
                fg=self.COLORS['text_white'],
                font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 15))
        
        var = tk.StringVar(value=default)
        
        # Guardar variable según el label
        if "FPS" in label:
            self.fps_var = var
        elif "CRF" in label:
            self.crf_var = var
        elif "Preset" in label:
            self.preset_var = var
        elif "Interval" in label:
            self.interval_var = var
            
        combo = ttk.Combobox(frame, textvariable=var, values=values,
                            width=15, state='readonly')
        combo.pack(side=tk.LEFT)
    
    # ==================== MÉTODOS DE FUNCIONALIDAD ====================
    
    def start_monitoring(self):
        """Inicia el monitoreo"""
        self.is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL, bg=self.COLORS['danger'])
        self.update_status("MONITORING", self.COLORS['warning'])
        self.log("✓ MONITORING STARTED - Waiting for ACC...")
        
        self.monitor_thread = threading.Thread(target=self.monitor_acc, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_monitoring = False
        
        if self.is_recording:
            self.stop_recording()
            
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED, bg=self.COLORS['bg_light'])
        self.update_status("OFFLINE", self.COLORS['danger'])
        self.log("✗ MONITORING STOPPED")
        
    def update_status(self, text, color):
        """Actualiza el indicador de estado"""
        self.status_text.config(text=text)
        self.status_indicator.itemconfig("indicator", fill=color)
        
    def log(self, message):
        """Añade mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
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
    
    # Métodos placeholder para funcionalidad completa
    def monitor_acc(self):
        self.log("ACC monitoring thread started...")
        
    def start_recording(self):
        self.is_recording = True
        self.recording_start_time = datetime.now()
        self.update_status("RECORDING", self.COLORS['accent_green'])
        
    def stop_recording(self):
        self.is_recording = False
        
    def refresh_recordings(self):
        for item in self.recordings_tree.get_children():
            self.recordings_tree.delete(item)
        self.log("Recordings list refreshed")
        
    def open_recordings_folder(self):
        os.startfile(self.output_dir)
        
    def play_selected_video(self):
        self.log("Play video...")
        
    def view_selected_telemetry(self):
        self.log("View telemetry...")
        
    def load_telemetry_json(self):
        self.log("Load JSON...")
        
    def open_web_viewer(self):
        self.log("Open web viewer...")
        
    def save_config(self):
        messagebox.showinfo("Configuration", "Configuration saved!")


def main():
    root = tk.Tk()
    app = ModernF1GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
