"""
Pestaña de Análisis Avanzado de Telemetría - Comparación de Vueltas
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QSlider, QListWidget,
                               QCheckBox, QComboBox, QGroupBox,
                               QFileDialog, QMessageBox, QScrollArea,
                               QListWidgetItem, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter, QColor, QPen
from pathlib import Path
import json
from typing import List

from gui.widgets import ModernButton
from gui.styles import COLORS, PANEL_STYLE


class TelemetryAnalysisTab(QWidget):
    """Pestaña de análisis avanzado con comparación de vueltas"""
    
    def __init__(self, output_dir: Path):
        super().__init__()
        self.output_dir = output_dir
        self.telemetry_data = []
        self.laps_data = {}
        self.current_time_index = 0
        self.selected_laps = []
        self.charts = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        
        header = self.create_header()
        main_layout.addWidget(header)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def create_header(self) -> QWidget:
        """Crea el header con controles de carga"""
        widget = QFrame()
        widget.setStyleSheet(PANEL_STYLE)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        
        btn_load = ModernButton("📂 Cargar Telemetría", primary=True)
        btn_load.clicked.connect(self.load_telemetry)
        layout.addWidget(btn_load)
        
        self.file_label = QLabel("No hay archivo cargado")
        self.file_label.setStyleSheet("color: #718096; font-size: 13px;")
        layout.addWidget(self.file_label)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_left_panel(self) -> QWidget:
        """Panel izquierdo: Lista de vueltas y controles"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        laps_group = self.create_laps_list()
        layout.addWidget(laps_group)
        
        compare_group = self.create_compare_controls()
        layout.addWidget(compare_group)
        
        timeline_group = self.create_timeline_controls()
        layout.addWidget(timeline_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_laps_list(self) -> QGroupBox:
        """Crea la lista de vueltas"""
        group = QGroupBox("Vueltas Disponibles")
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {COLORS['panel_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        self.laps_list = QListWidget()
        self.laps_list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS['input_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
                color: {COLORS['text_primary']};
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background: {COLORS['accent']};
                color: white;
            }}
            QListWidget::item:hover {{
                background: {COLORS['panel_hover']};
            }}
        """)
        self.laps_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.laps_list.itemSelectionChanged.connect(self.on_lap_selection_changed)
        
        layout.addWidget(self.laps_list)
        
        btn_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("Todas")
        self.btn_select_all.clicked.connect(self.select_all_laps)
        
        self.btn_clear = QPushButton("Ninguna")
        self.btn_clear.clicked.connect(self.clear_lap_selection)
        
        for btn in [self.btn_select_all, self.btn_clear]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['button_bg']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {COLORS['button_hover']};
                }}
            """)
        
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_clear)
        
        layout.addLayout(btn_layout)
        
        group.setLayout(layout)
        return group
    
    def create_compare_controls(self) -> QGroupBox:
        """Controles de comparación"""
        group = QGroupBox("Opciones de Comparación")
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {COLORS['panel_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        sort_layout = QHBoxLayout()
        sort_label = QLabel("Ordenar por:")
        sort_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Número de vuelta",
            "Tiempo (más rápida primero)",
            "Tiempo (más lenta primero)"
        ])
        self.sort_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent']};
            }}
        """)
        self.sort_combo.currentIndexChanged.connect(self.sort_laps)
        
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_combo, 1)
        
        layout.addLayout(sort_layout)
        
        self.align_time_check = QCheckBox("Alinear vueltas por tiempo relativo")
        self.align_time_check.setChecked(True)
        self.align_time_check.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_primary']};
                font-size: 12px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid {COLORS['border']};
                background: {COLORS['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
        """)
        self.align_time_check.stateChanged.connect(self.update_charts)
        
        layout.addWidget(self.align_time_check)
        
        self.btn_update = ModernButton("🔄 Actualizar Gráficos")
        self.btn_update.clicked.connect(self.update_charts)
        layout.addWidget(self.btn_update)
        
        group.setLayout(layout)
        return group
    
    def create_timeline_controls(self) -> QGroupBox:
        """Controles de timeline/slider"""
        group = QGroupBox("Timeline")
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {COLORS['panel_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        self.time_display = QLabel("00:00.000")
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_display.setStyleSheet(f"""
            color: {COLORS['accent']};
            font-size: 24px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(self.time_display)
        
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.setValue(0)
        self.timeline_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border']};
                height: 8px;
                background: {COLORS['input_bg']};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                border: 2px solid {COLORS['accent']};
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent']};
                border-radius: 4px;
            }}
        """)
        self.timeline_slider.valueChanged.connect(self.on_timeline_changed)
        layout.addWidget(self.timeline_slider)
        
        range_layout = QHBoxLayout()
        self.start_time_label = QLabel("00:00")
        self.end_time_label = QLabel("00:00")
        
        for lbl in [self.start_time_label, self.end_time_label]:
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        
        range_layout.addWidget(self.start_time_label)
        range_layout.addStretch()
        range_layout.addWidget(self.end_time_label)
        layout.addLayout(range_layout)
        
        self.current_info_label = QLabel("")
        self.current_info_label.setWordWrap(True)
        self.current_info_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 12px;
            padding: 8px;
            background: {COLORS['input_bg']};
            border-radius: 4px;
        """)
        layout.addWidget(self.current_info_label)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self) -> QWidget:
        """Panel derecho: Gráficos"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)
        
        self.create_chart_views(layout)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        
        return scroll
    
    def create_chart_views(self, layout: QVBoxLayout):
        """Crea las vistas de gráficos"""
        chart_configs = [
            ("speed_chart", "Velocidad (km/h)"),
            ("rpm_chart", "RPM"),
            ("throttle_brake_chart", "Acelerador / Freno"),
            ("gforce_chart", "Fuerzas G (Lateral / Longitudinal)"),
            ("wheel_slip_chart", "Deslizamiento de Ruedas"),
            ("tyre_temp_chart", "Temperatura de Neumáticos (°C)"),
            ("brake_temp_chart", "Temperatura de Frenos (°C)"),
        ]
        
        for chart_id, title in chart_configs:
            chart_view = self.create_chart(title)
            self.charts[chart_id] = chart_view
            layout.addWidget(chart_view)
    
    def create_chart(self, title: str) -> QChartView:
        """Crea un gráfico vacío"""
        chart = QChart()
        chart.setTitle(title)
        chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
        
        axis_x = QValueAxis()
        axis_x.setTitleText("Tiempo (s)")
        axis_y = QValueAxis()
        
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(300)
        
        return chart_view
    
    def load_telemetry(self):
        """Carga archivo de telemetría"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de telemetría",
            str(self.output_dir),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.telemetry_data = json.load(f)
            
            self.file_label.setText(f"✓ {Path(filename).name} - {len(self.telemetry_data)} registros")
            self.file_label.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 13px; font-weight: 500;")
            
            self.process_laps()
            self.populate_laps_list()
            self.update_timeline_range()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo:\\n{str(e)}")
    
    def process_laps(self):
        """Procesa la telemetría y detecta vueltas"""
        self.laps_data = {}
        
        if not self.telemetry_data:
            return
        
        current_lap = None
        lap_start_idx = 0
        
        for i, record in enumerate(self.telemetry_data):
            lap_num = record.get('lap_number', 0)
            
            if current_lap is None:
                current_lap = lap_num
                lap_start_idx = i
            
            if lap_num != current_lap:
                lap_data = self.telemetry_data[lap_start_idx:i]
                lap_time = self.calculate_lap_time(lap_data)
                
                self.laps_data[current_lap] = {
                    'start_idx': lap_start_idx,
                    'end_idx': i - 1,
                    'lap_time': lap_time,
                    'data': lap_data
                }
                
                current_lap = lap_num
                lap_start_idx = i
        
        if current_lap is not None:
            lap_data = self.telemetry_data[lap_start_idx:]
            lap_time = self.calculate_lap_time(lap_data)
            
            self.laps_data[current_lap] = {
                'start_idx': lap_start_idx,
                'end_idx': len(self.telemetry_data) - 1,
                'lap_time': lap_time,
                'data': lap_data
            }
    
    def calculate_lap_time(self, lap_data: List[dict]) -> float:
        """Calcula el tiempo de una vuelta"""
        if not lap_data or len(lap_data) < 2:
            return 0.0
        
        start_time = lap_data[0].get('second', 0)
        end_time = lap_data[-1].get('second', 0)
        
        return end_time - start_time
    
    def populate_laps_list(self):
        """Puebla la lista de vueltas"""
        self.laps_list.clear()
        
        for lap_num in sorted(self.laps_data.keys()):
            lap_info = self.laps_data[lap_num]
            lap_time = lap_info['lap_time']
            
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            
            item_text = f"Vuelta {lap_num}: {minutes:02d}:{seconds:06.3f}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, lap_num)
            
            self.laps_list.addItem(item)
    
    def update_timeline_range(self):
        """Actualiza el rango del timeline"""
        if not self.telemetry_data:
            return
        
        max_idx = len(self.telemetry_data) - 1
        self.timeline_slider.setMaximum(max_idx)
        
        total_seconds = self.telemetry_data[-1].get('second', 0)
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        self.end_time_label.setText(f"{minutes:02d}:{seconds:05.2f}")
    
    def on_lap_selection_changed(self):
        """Cuando cambia la selección de vueltas"""
        self.selected_laps = []
        
        for item in self.laps_list.selectedItems():
            lap_num = item.data(Qt.ItemDataRole.UserRole)
            self.selected_laps.append(lap_num)
        
        self.update_charts()
    
    def select_all_laps(self):
        """Selecciona todas las vueltas"""
        self.laps_list.selectAll()
    
    def clear_lap_selection(self):
        """Limpia la selección"""
        self.laps_list.clearSelection()
    
    def sort_laps(self):
        """Ordena las vueltas según criterio"""
        sort_type = self.sort_combo.currentIndex()
        
        if sort_type == 0:
            sorted_laps = sorted(self.laps_data.keys())
        elif sort_type == 1:
            sorted_laps = sorted(self.laps_data.keys(), 
                               key=lambda x: self.laps_data[x]['lap_time'])
        else:
            sorted_laps = sorted(self.laps_data.keys(), 
                               key=lambda x: self.laps_data[x]['lap_time'], 
                               reverse=True)
        
        self.laps_list.clear()
        for lap_num in sorted_laps:
            lap_info = self.laps_data[lap_num]
            lap_time = lap_info['lap_time']
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            
            item_text = f"Vuelta {lap_num}: {minutes:02d}:{seconds:06.3f}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, lap_num)
            self.laps_list.addItem(item)
    
    def on_timeline_changed(self, value: int):
        """Cuando cambia el slider de timeline"""
        self.current_time_index = value
        
        if not self.telemetry_data or value >= len(self.telemetry_data):
            return
        
        current_second = self.telemetry_data[value].get('second', 0)
        minutes = int(current_second // 60)
        seconds = current_second % 60
        milliseconds = int((seconds % 1) * 1000)
        
        self.time_display.setText(f"{minutes:02d}:{int(seconds):02d}.{milliseconds:03d}")
        
        self.update_current_info(value)
    
    def update_current_info(self, index: int):
        """Actualiza la información del punto actual"""
        if index >= len(self.telemetry_data):
            return
        
        record = self.telemetry_data[index]
        telemetry = record.get('player_telemetry', {})
        
        info_lines = []
        info_lines.append(f"Vuelta: {record.get('lap_number', 'N/A')}")
        info_lines.append(f"Velocidad: {telemetry.get('speed_kmh', 0):.1f} km/h")
        info_lines.append(f"RPM: {telemetry.get('rpm', 0)}")
        info_lines.append(f"Marcha: {telemetry.get('gear', 0)}")
        
        self.current_info_label.setText("\\n".join(info_lines))
    
    def update_charts(self):
        """Actualiza todos los gráficos con las vueltas seleccionadas"""
        if not self.selected_laps:
            self.clear_all_charts()
            return
        
        align_time = self.align_time_check.isChecked()
        
        colors = [
            QColor(255, 68, 68),
            QColor(68, 138, 255),
            QColor(76, 209, 55),
            QColor(255, 152, 0),
            QColor(156, 39, 176),
            QColor(0, 188, 212),
            QColor(255, 235, 59),
            QColor(121, 85, 72),
        ]
        
        self.update_speed_chart(colors, align_time)
        self.update_rpm_chart(colors, align_time)
    
    def clear_all_charts(self):
        """Limpia todos los gráficos"""
        for chart_view in self.charts.values():
            chart = chart_view.chart()
            chart.removeAllSeries()
    
    def update_speed_chart(self, colors: List[QColor], align_time: bool):
        """Actualiza gráfico de velocidad"""
        chart_view = self.charts.get('speed_chart')
        if not chart_view:
            return
        
        chart = chart_view.chart()
        chart.removeAllSeries()
        
        for i, lap_num in enumerate(self.selected_laps):
            lap_data = self.laps_data[lap_num]['data']
            
            series = QLineSeries()
            series.setName(f"Vuelta {lap_num}")
            
            color = colors[i % len(colors)]
            pen = QPen(color)
            pen.setWidth(2)
            series.setPen(pen)
            
            for j, record in enumerate(lap_data):
                telemetry = record.get('player_telemetry', {})
                speed = telemetry.get('speed_kmh', 0)
                
                if align_time:
                    x = j * 0.1
                else:
                    x = record.get('second', 0)
                
                series.append(x, speed)
            
            chart.addSeries(series)
            series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
            series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
        
        self.adjust_chart_axes(chart)
    
    def update_rpm_chart(self, colors: List[QColor], align_time: bool):
        """Actualiza gráfico de RPM"""
        chart_view = self.charts.get('rpm_chart')
        if not chart_view:
            return
        
        chart = chart_view.chart()
        chart.removeAllSeries()
        
        for i, lap_num in enumerate(self.selected_laps):
            lap_data = self.laps_data[lap_num]['data']
            
            series = QLineSeries()
            series.setName(f"Vuelta {lap_num}")
            
            color = colors[i % len(colors)]
            pen = QPen(color)
            pen.setWidth(2)
            series.setPen(pen)
            
            for j, record in enumerate(lap_data):
                telemetry = record.get('player_telemetry', {})
                rpm = telemetry.get('rpm', 0)
                
                if align_time:
                    x = j * 0.1
                else:
                    x = record.get('second', 0)
                
                series.append(x, rpm)
            
            chart.addSeries(series)
            series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
            series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
        
        self.adjust_chart_axes(chart)
    
    def adjust_chart_axes(self, chart: QChart):
        """Ajusta los ejes del gráfico automáticamente"""
        if not chart.series():
            return
        
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        for series in chart.series():
            if not isinstance(series, QLineSeries):
                continue
            
            points = series.pointsVector()
            for point in points:
                min_x = min(min_x, point.x())
                max_x = max(max_x, point.x())
                min_y = min(min_y, point.y())
                max_y = max(max_y, point.y())
        
        if min_x != float('inf') and max_x != float('-inf'):
            x_axis = chart.axes(Qt.Orientation.Horizontal)[0]
            x_axis.setRange(min_x, max_x)
        
        if min_y != float('inf') and max_y != float('-inf'):
            y_axis = chart.axes(Qt.Orientation.Vertical)[0]
            margin = (max_y - min_y) * 0.1
            y_axis.setRange(min_y - margin, max_y + margin)
