"""
ACC Race Recorder - Modern Qt6 GUI
Punto de entrada principal (MODULAR)
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    # Configurar fuente global
    font = QFont("SF Pro Display", 10)
    if font.family() != "SF Pro Display":
        font = QFont("Segoe UI", 10)  # Fallback para Windows
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
