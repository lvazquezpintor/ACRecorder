"""
Widgets reutilizables para la GUI moderna
"""

from PySide6.QtWidgets import QPushButton, QLabel, QFrame, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter


class ModernButton(QPushButton):
    """Botón moderno personalizado"""
    def __init__(self, text: str, primary: bool = False, danger: bool = False, success: bool = False):
        super().__init__(text)
        self.primary = primary
        self.danger = danger
        self.success = success
        self.setup_style()
        
    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2D3748;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #1A202C;
                }
                QPushButton:disabled {
                    background-color: #E2E8F0;
                    color: #A0AEC0;
                }
            """)
        elif self.success:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #48BB78;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #38A169;
                }
            """)
        elif self.danger:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F7FAFC;
                    color: #4A5568;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #EDF2F7;
                    border-color: #CBD5E0;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F7FAFC;
                    color: #4A5568;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #EDF2F7;
                }
            """)


class SidebarButton(QPushButton):
    """Botón de navegación lateral"""
    def __init__(self, icon_text: str, text: str):
        super().__init__(f"{icon_text}  {text}")
        self.setCheckable(True)
        self.setup_style()
        
    def setup_style(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A5568;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F7FAFC;
            }
            QPushButton:checked {
                background-color: #F7FAFC;
                border-left: 3px solid #E53E3E;
                color: #2D3748;
            }
        """)


class StatusIndicator(QWidget):
    """Indicador de estado circular"""
    def __init__(self, color: str = "#EF4444"):
        super().__init__()
        self.color = color
        self.setFixedSize(12, 12)
        
    def set_color(self, color: str):
        self.color = color
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 12, 12)


class DataCard(QFrame):
    """Tarjeta de datos"""
    def __init__(self, label: str, value: str = "—"):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #718096; font-size: 12px; font-weight: 500;")
        
        self.value_widget = QLabel(value)
        self.value_widget.setStyleSheet("color: #2D3748; font-size: 20px; font-weight: 600;")
        
        layout.addWidget(label_widget)
        layout.addWidget(self.value_widget)
        self.setLayout(layout)
        
    def set_value(self, value: str):
        self.value_widget.setText(str(value))
