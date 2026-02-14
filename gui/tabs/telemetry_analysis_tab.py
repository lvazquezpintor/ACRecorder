"""
Pestaña de Análisis Avanzado de Telemetría - Comparación de Vueltas y Análisis de Sectores
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QSlider, QListWidget,
                               QCheckBox, QComboBox, QGroupBox,
                               QFileDialog, QMessageBox, QScrollArea,
                               QListWidgetItem, QSplitter, QTableWidget,
                               QTableWidgetItem, QHeaderView, QSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QBarSeries, QBarSet, QBarCategoryAxis
from PySide6.QtGui import QPainter, QColor, QPen
from pathlib import Path
import json
from typing import List, Dict, Tuple
from datetime import datetime
import statistics

from gui.widgets import ModernButton
from gui.widgets.track_map_widget import TrackMapWidget, generate_track_from_telemetry
from gui.styles import COLORS, PANEL_STYLE


class LapAnalyzer:
    """Analiza vueltas y calcula deltas por sectores"""
    
    def __init__(self, telemetry_data: List[Dict]):
        self.telemetry_data = telemetry_data
        self.laps = self._extract_laps()
        
    def _extract_laps(self) -> Dict[int, List[Dict]]:
        """Extrae cada vuelta como una lista de registros"""
        laps = {}
        current_lap = None
        lap_records = []
        
        for record in self.telemetry_data:
            session = record.get('session_info', {})
            lap_num = session.get('completed_laps', 0)
            
            if current_lap is None:
                current_lap = lap_num
            elif lap_num != current_lap:
                if lap_records and current_lap > 0:
                    laps[current_lap] = lap_records.copy()
                lap_records = []
                current_lap = lap_num
            
            lap_records.append(record)
        
        if lap_records and current_lap and current_lap > 0:
            laps[current_lap] = lap_records
        
        return laps
    
    def get_lap_time(self, lap_number: int) -> float:
        """Calcula el tiempo de una vuelta"""
        if lap_number not in self.laps:
            return 0.0
        
        lap_records = self.laps[lap_number]
        if len(lap_records) < 2:
            return 0.0
        
        start_time = datetime.fromisoformat(lap_records[0]['timestamp'])
        end_time = datetime.fromisoformat(lap_records[-1]['timestamp'])
        
        return (end_time - start_time).total_seconds()
    
    def find_best_lap(self) -> Tuple[int, float]:
        """Encuentra la mejor vuelta"""
        best_lap = None
        best_time = float('inf')
        
        for lap_num in self.laps.keys():
            lap_time = self.get_lap_time(lap_num)
            if 0 < lap_time < best_time:
                best_time = lap_time
                best_lap = lap_num
        
        return best_lap, best_time
    
    def divide_lap_into_segments(self, lap_number: int, num_segments: int = 10) -> List[List[Dict]]:
        """Divide una vuelta en N segmentos basados en normalized_position"""
        if lap_number not in self.laps:
            return []
        
        lap_records = self.laps[lap_number]
        segments = [[] for _ in range(num_segments)]
        
        for record in lap_records:
            session = record.get('session_info', {})
            normalized_pos = session.get('normalized_position', 0.0)
            
            segment_idx = min(int(normalized_pos * num_segments), num_segments - 1)
            segments[segment_idx].append(record)
        
        return segments
    
    def get_segment_time(self, segment_records: List[Dict]) -> float:
        """Calcula el tiempo de un segmento"""
        if len(segment_records) < 2:
            return 0.0
        
        start_time = datetime.fromisoformat(segment_records[0]['timestamp'])
        end_time = datetime.fromisoformat(segment_records[-1]['timestamp'])
        
        return (end_time - start_time).total_seconds()
    
    def get_segment_stats(self, segment_records: List[Dict]) -> Dict:
        """Calcula estadísticas de un segmento"""
        if not segment_records:
            return {}
        
        speeds = []
        brake_usage = []
        throttle_usage = []
        min_speed = float('inf')
        max_speed = 0.0
        
        for record in segment_records:
            player = record.get('player_telemetry', {})
            if player:
                speed = player.get('speed_kmh', 0)
                speeds.append(speed)
                min_speed = min(min_speed, speed)
                max_speed = max(max_speed, speed)
                
                brake_usage.append(player.get('brake', 0))
                throttle_usage.append(player.get('gas', 0))
        
        return {
            'avg_speed': statistics.mean(speeds) if speeds else 0,
            'min_speed': min_speed if min_speed != float('inf') else 0,
            'max_speed': max_speed,
            'avg_brake': statistics.mean(brake_usage) if brake_usage else 0,
            'avg_throttle': statistics.mean(throttle_usage) if throttle_usage else 0,
            'time': self.get_segment_time(segment_records)
        }
    
    def compare_laps(self, lap1: int, lap2: int, num_segments: int = 10) -> List[Dict]:
        """Compara dos vueltas segmento por segmento"""
        segments1 = self.divide_lap_into_segments(lap1, num_segments)
        segments2 = self.divide_lap_into_segments(lap2, num_segments)
        
        comparison = []
        cumulative_delta = 0.0
        
        for i in range(num_segments):
            if i >= len(segments1) or i >= len(segments2):
                continue
            
            stats1 = self.get_segment_stats(segments1[i])
            stats2 = self.get_segment_stats(segments2[i])
            
            segment_delta = stats2['time'] - stats1['time']
            cumulative_delta += segment_delta
            
            comparison.append({
                'segment': i + 1,
                'percentage': f"{i*10}-{(i+1)*10}%",
                'lap1_time': stats1['time'],
                'lap2_time': stats2['time'],
                'delta': segment_delta,
                'cumulative_delta': cumulative_delta,
                'lap1_avg_speed': stats1['avg_speed'],
                'lap2_avg_speed': stats2['avg_speed'],
                'speed_diff': stats2['avg_speed'] - stats1['avg_speed'],
                'lap1_min_speed': stats1['min_speed'],
                'lap2_min_speed': stats2['min_speed']
            })
        
        return comparison


class TelemetryAnalysisTab(QWidget):
    """Pestaña de análisis avanzado con comparación de vueltas y análisis de sectores"""
    
    def __init__(self, output_dir: Path):
        super().__init__()
        self.output_dir = output_dir
        self.telemetry_data = []
        self.analyzer = None
        self.best_lap_num = None
        self.num_segments = 10
        self.selected_lap_num = None
        
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
        
        self.best_lap_label = QLabel("")
        self.best_lap_label.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 13px; font-weight: 600;")
        layout.addWidget(self.best_lap_label)
        
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
        
        sector_group = self.create_sector_controls()
        layout.addWidget(sector_group)
        
        compare_group = self.create_compare_controls()
        layout.addWidget(compare_group)
        
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
        self.laps_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.laps_list.itemSelectionChanged.connect(self.on_lap_selection_changed)
        
        layout.addWidget(self.laps_list)
        
        group.setLayout(layout)
        return group
    
    def create_sector_controls(self) -> QGroupBox:
        """Controles de análisis por sectores"""
        group = QGroupBox("Análisis por Sectores")
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
        """)
        
        layout = QVBoxLayout()
        
        # Número de segmentos
        segments_layout = QHBoxLayout()
        segments_label = QLabel("Dividir vuelta en:")
        segments_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px;")
        
        self.segments_spinbox = QSpinBox()
        self.segments_spinbox.setMinimum(5)
        self.segments_spinbox.setMaximum(20)
        self.segments_spinbox.setValue(10)
        self.segments_spinbox.setSuffix(" sectores")
        self.segments_spinbox.setStyleSheet(f"""
            QSpinBox {{
                background: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        self.segments_spinbox.valueChanged.connect(self.on_segments_changed)
        
        segments_layout.addWidget(segments_label)
        segments_layout.addWidget(self.segments_spinbox)
        
        layout.addLayout(segments_layout)
        
        # Botón de análisis
        self.btn_analyze = ModernButton("🔍 Analizar vs Mejor Vuelta")
        self.btn_analyze.clicked.connect(self.analyze_selected_lap)
        self.btn_analyze.setEnabled(False)
        layout.addWidget(self.btn_analyze)
        
        group.setLayout(layout)
        return group
    
    def create_compare_controls(self) -> QGroupBox:
        """Controles de comparación"""
        group = QGroupBox("Opciones de Visualización")
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
        """)
        self.sort_combo.currentIndexChanged.connect(self.sort_laps)
        
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_combo, 1)
        
        layout.addLayout(sort_layout)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self) -> QWidget:
        """Panel derecho: Mapa, Tabla de deltas y gráficos"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)
        
        # Mapa del circuito 2D
        self.track_map = TrackMapWidget()
        self.track_map.setMinimumHeight(500)
        self.track_map.sector_clicked.connect(self.on_sector_clicked)
        layout.addWidget(self.track_map)
        
        # Tabla de deltas por sector
        self.delta_table = self.create_delta_table()
        layout.addWidget(self.delta_table)
        
        # Gráfico de deltas
        self.delta_chart_view = self.create_delta_chart()
        layout.addWidget(self.delta_chart_view)
        
        # Gráfico de velocidades comparadas
        self.speed_comparison_chart = self.create_speed_comparison_chart()
        layout.addWidget(self.speed_comparison_chart)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        
        return scroll
    
    def create_delta_table(self) -> QTableWidget:
        """Crea la tabla de deltas por sector"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Sector", "Zona", "Delta", "Acumulado", "Vel. Media", "Vel. Mín"
        ])
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['panel_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {COLORS['accent']};
            }}
            QHeaderView::section {{
                background: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                padding: 8px;
                border: none;
                font-weight: 600;
            }}
        """)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(400)
        table.setMaximumHeight(500)
        
        return table
    
    def create_delta_chart(self) -> QChartView:
        """Crea el gráfico de barras de deltas"""
        chart = QChart()
        chart.setTitle("Deltas por Sector (vs Mejor Vuelta)")
        chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(400)
        
        return chart_view
    
    def create_speed_comparison_chart(self) -> QChartView:
        """Crea gráfico de comparación de velocidades"""
        chart = QChart()
        chart.setTitle("Comparación de Velocidad por Posición en el Circuito")
        chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        
        axis_x = QValueAxis()
        axis_x.setTitleText("Posición en Circuito (%)")
        axis_y = QValueAxis()
        axis_y.setTitleText("Velocidad (km/h)")
        
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(400)
        
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
            
            # Crear analizador
            self.analyzer = LapAnalyzer(self.telemetry_data)
            
            # Encontrar mejor vuelta
            self.best_lap_num, best_time = self.analyzer.find_best_lap()
            if self.best_lap_num:
                self.best_lap_label.setText(f"🏆 Mejor: Vuelta #{self.best_lap_num} - {best_time:.3f}s")
                
                # Generar mapa del circuito usando la mejor vuelta
                track_points = generate_track_from_telemetry(self.analyzer.laps[self.best_lap_num])
                
                # Obtener nombre del circuito
                track_name = "Circuito Desconocido"
                if self.telemetry_data:
                    track_data = self.telemetry_data[0].get('track_data', {})
                    if track_data:
                        track_name = track_data.get('track_name', 'Circuito Desconocido')
                
                self.track_map.set_track_data(track_points, track_name)
            
            self.populate_laps_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo:\n{str(e)}")
    
    def populate_laps_list(self):
        """Puebla la lista de vueltas"""
        self.laps_list.clear()
        
        if not self.analyzer:
            return
        
        for lap_num in sorted(self.analyzer.laps.keys()):
            lap_time = self.analyzer.get_lap_time(lap_num)
            
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            
            # Calcular delta vs mejor
            if self.best_lap_num:
                best_time = self.analyzer.get_lap_time(self.best_lap_num)
                delta = lap_time - best_time
                delta_str = f" (+{delta:.3f}s)" if delta > 0 else " (BEST)"
            else:
                delta_str = ""
            
            item_text = f"Vuelta {lap_num}: {minutes:02d}:{seconds:06.3f}{delta_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, lap_num)
            
            # Resaltar mejor vuelta
            if lap_num == self.best_lap_num:
                item.setForeground(QColor(COLORS['accent_green']))
            
            self.laps_list.addItem(item)
    
    def on_lap_selection_changed(self):
        """Cuando cambia la selección de vuelta"""
        selected_items = self.laps_list.selectedItems()
        
        if selected_items:
            self.selected_lap_num = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.btn_analyze.setEnabled(True)
        else:
            self.selected_lap_num = None
            self.btn_analyze.setEnabled(False)
    
    def on_segments_changed(self, value: int):
        """Cuando cambia el número de segmentos"""
        self.num_segments = value
    
    def on_sector_clicked(self, sector_idx: int):
        """Cuando se hace click en un sector del mapa"""
        if not self.delta_table or self.delta_table.rowCount() == 0:
            return
        
        # Seleccionar la fila correspondiente en la tabla
        self.delta_table.selectRow(sector_idx)
        self.delta_table.scrollToItem(self.delta_table.item(sector_idx, 0))
    
    def sort_laps(self):
        """Ordena las vueltas según criterio"""
        if not self.analyzer:
            return
        
        sort_type = self.sort_combo.currentIndex()
        
        if sort_type == 0:
            sorted_laps = sorted(self.analyzer.laps.keys())
        elif sort_type == 1:
            sorted_laps = sorted(self.analyzer.laps.keys(), 
                               key=lambda x: self.analyzer.get_lap_time(x))
        else:
            sorted_laps = sorted(self.analyzer.laps.keys(), 
                               key=lambda x: self.analyzer.get_lap_time(x), 
                               reverse=True)
        
        self.laps_list.clear()
        for lap_num in sorted_laps:
            lap_time = self.analyzer.get_lap_time(lap_num)
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            
            if self.best_lap_num:
                best_time = self.analyzer.get_lap_time(self.best_lap_num)
                delta = lap_time - best_time
                delta_str = f" (+{delta:.3f}s)" if delta > 0 else " (BEST)"
            else:
                delta_str = ""
            
            item_text = f"Vuelta {lap_num}: {minutes:02d}:{seconds:06.3f}{delta_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, lap_num)
            
            if lap_num == self.best_lap_num:
                item.setForeground(QColor(COLORS['accent_green']))
            
            self.laps_list.addItem(item)
    
    def analyze_selected_lap(self):
        """Analiza la vuelta seleccionada vs la mejor"""
        if not self.selected_lap_num or not self.analyzer or not self.best_lap_num:
            return
        
        if self.selected_lap_num == self.best_lap_num:
            QMessageBox.information(
                self,
                "Info",
                "Esta es la mejor vuelta. Selecciona otra vuelta para comparar."
            )
            return
        
        # Comparar vueltas
        comparison = self.analyzer.compare_laps(
            self.best_lap_num,
            self.selected_lap_num,
            self.num_segments
        )
        
        # Actualizar mapa con deltas
        deltas = [seg['delta'] for seg in comparison]
        sector_data = [
            {
                'avg_speed': seg['lap2_avg_speed'],
                'min_speed': seg['lap2_min_speed']
            }
            for seg in comparison
        ]
        self.track_map.set_sector_analysis(self.num_segments, deltas, sector_data)
        
        # Actualizar tabla
        self.update_delta_table(comparison)
        
        # Actualizar gráfico de deltas
        self.update_delta_chart(comparison)
        
        # Actualizar gráfico de velocidades
        self.update_speed_comparison(self.selected_lap_num)
    
    def update_delta_table(self, comparison: List[Dict]):
        """Actualiza la tabla de deltas"""
        self.delta_table.setRowCount(len(comparison))
        
        for i, seg in enumerate(comparison):
            # Sector
            self.delta_table.setItem(i, 0, QTableWidgetItem(str(seg['segment'])))
            
            # Zona
            self.delta_table.setItem(i, 1, QTableWidgetItem(seg['percentage']))
            
            # Delta
            delta_str = f"+{seg['delta']:.3f}s" if seg['delta'] > 0 else f"{seg['delta']:.3f}s"
            delta_item = QTableWidgetItem(delta_str)
            if seg['delta'] > 0:
                delta_item.setForeground(QColor(255, 68, 68))  # Rojo si pierdes
            else:
                delta_item.setForeground(QColor(76, 209, 55))  # Verde si ganas
            self.delta_table.setItem(i, 2, delta_item)
            
            # Acumulado
            cumul_str = f"+{seg['cumulative_delta']:.3f}s" if seg['cumulative_delta'] > 0 else f"{seg['cumulative_delta']:.3f}s"
            cumul_item = QTableWidgetItem(cumul_str)
            if seg['cumulative_delta'] > 0:
                cumul_item.setForeground(QColor(255, 152, 0))
            self.delta_table.setItem(i, 3, cumul_item)
            
            # Velocidad media
            speed_diff = seg['speed_diff']
            speed_str = f"{speed_diff:+.1f} km/h"
            speed_item = QTableWidgetItem(speed_str)
            if speed_diff < 0:
                speed_item.setForeground(QColor(255, 68, 68))
            self.delta_table.setItem(i, 4, speed_item)
            
            # Velocidad mínima
            min_speed_str = f"{seg['lap2_min_speed']:.1f} km/h"
            self.delta_table.setItem(i, 5, QTableWidgetItem(min_speed_str))
    
    def update_delta_chart(self, comparison: List[Dict]):
        """Actualiza el gráfico de barras de deltas"""
        chart = self.delta_chart_view.chart()
        chart.removeAllSeries()
        
        # Crear barras
        positive_set = QBarSet("Pierdes tiempo")
        negative_set = QBarSet("Ganas tiempo")
        
        positive_set.setColor(QColor(255, 68, 68))
        negative_set.setColor(QColor(76, 209, 55))
        
        categories = []
        
        for seg in comparison:
            categories.append(f"S{seg['segment']}")
            
            if seg['delta'] > 0:
                positive_set.append(seg['delta'])
                negative_set.append(0)
            else:
                positive_set.append(0)
                negative_set.append(abs(seg['delta']))
        
        series = QBarSeries()
        series.append(positive_set)
        series.append(negative_set)
        
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Eje X con categorías
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        # Eje Y
        axis_y = QValueAxis()
        axis_y.setTitleText("Delta (segundos)")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
    
    def update_speed_comparison(self, lap_num: int):
        """Actualiza gráfico de comparación de velocidades"""
        chart = self.speed_comparison_chart.chart()
        chart.removeAllSeries()
        
        # Serie de mejor vuelta
        best_series = QLineSeries()
        best_series.setName(f"Vuelta #{self.best_lap_num} (Mejor)")
        best_pen = QPen(QColor(76, 209, 55))
        best_pen.setWidth(2)
        best_series.setPen(best_pen)
        
        best_lap_records = self.analyzer.laps[self.best_lap_num]
        for record in best_lap_records:
            session = record.get('session_info', {})
            player = record.get('player_telemetry', {})
            
            pos = session.get('normalized_position', 0.0) * 100
            speed = player.get('speed_kmh', 0)
            
            best_series.append(pos, speed)
        
        # Serie de vuelta seleccionada
        lap_series = QLineSeries()
        lap_series.setName(f"Vuelta #{lap_num}")
        lap_pen = QPen(QColor(255, 68, 68))
        lap_pen.setWidth(2)
        lap_series.setPen(lap_pen)
        
        lap_records = self.analyzer.laps[lap_num]
        for record in lap_records:
            session = record.get('session_info', {})
            player = record.get('player_telemetry', {})
            
            pos = session.get('normalized_position', 0.0) * 100
            speed = player.get('speed_kmh', 0)
            
            lap_series.append(pos, speed)
        
        chart.addSeries(best_series)
        chart.addSeries(lap_series)
        
        # Conectar ejes
        best_series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        best_series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
        lap_series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        lap_series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
        
        # Ajustar ejes
        chart.axes(Qt.Orientation.Horizontal)[0].setRange(0, 100)
