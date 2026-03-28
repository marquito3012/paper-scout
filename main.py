"""
Paper Scout — Entry Point.

Aplicación de escritorio Linux para buscar papers en arXiv,
resumirlos con IA y guardarlos como notas de Obsidian.

Uso:
    source .venv/bin/activate
    python main.py
"""

import sys
import os

# Asegurar que el directorio del proyecto está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.views.main_window import MainWindow, DARK_THEME_QSS


def main():
    """Punto de entrada principal de la aplicación."""
    # Habilitar High DPI scaling para monitores modernos
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Paper Scout")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("paper-scout")
    
    # Aplicar tema oscuro global
    app.setStyleSheet(DARK_THEME_QSS)
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
