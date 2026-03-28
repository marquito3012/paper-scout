"""
main_window.py — Ventana principal de Paper Scout.

Interfaz gráfica premium con tema oscuro, diseñada para Linux.
Implementa el patrón Worker Object para ejecutar el pipeline
en segundo plano sin congelar la GUI (skills/pyqt6-async/SKILL.md).

Componentes:
  - Panel de configuración (keywords, vault, API key, provider)
  - Botones Start/Stop con estados visuales
  - Barra de progreso animada
  - Panel de logs con colores por severidad
  - Botón para abrir PDF del paper
"""

import webbrowser
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QSize
from PyQt6.QtGui import QFont, QIcon, QTextCursor, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.controllers.pipeline_controller import PipelineConfig, PipelineWorker
from src.utils.config_manager import load_config, save_config


# ──────────────────────────────────────────────────
# Paleta de colores premium (GitHub Dark-inspired)
# ──────────────────────────────────────────────────
COLORS = {
    "bg_primary": "#0D1117",
    "bg_secondary": "#161B22",
    "bg_tertiary": "#21262D",
    "border": "#30363D",
    "text_primary": "#E6EDF3",
    "text_secondary": "#8B949E",
    "accent_blue": "#58A6FF",
    "accent_green": "#238636",
    "accent_green_hover": "#2EA043",
    "accent_red": "#F85149",
    "accent_red_hover": "#DA3633",
    "accent_orange": "#D29922",
    "accent_purple": "#BC8CFF",
}


# ──────────────────────────────────────────────────
# Stylesheet global QSS (tema oscuro premium)
# ──────────────────────────────────────────────────
DARK_THEME_QSS = f"""
/* ─── Base ─── */
QMainWindow {{
    background-color: {COLORS["bg_primary"]};
}}

QWidget {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
    font-family: "Inter", "Segoe UI", "Roboto", sans-serif;
    font-size: 13px;
}}

/* ─── Group Boxes ─── */
QGroupBox {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px;
    padding-top: 28px;
    font-weight: bold;
    font-size: 14px;
    color: {COLORS["text_primary"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    color: {COLORS["accent_blue"]};
}}

/* ─── Labels ─── */
QLabel {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    background: transparent;
}}

/* ─── Input Fields ─── */
QLineEdit {{
    background-color: {COLORS["bg_tertiary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS["text_primary"]};
    font-size: 13px;
    selection-background-color: {COLORS["accent_blue"]};
}}

QLineEdit:focus {{
    border-color: {COLORS["accent_blue"]};
}}

QLineEdit:disabled {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_secondary"]};
}}

/* ─── SpinBox ─── */
QSpinBox {{
    background-color: {COLORS["bg_tertiary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS["text_primary"]};
    font-size: 13px;
}}

QSpinBox:focus {{
    border-color: {COLORS["accent_blue"]};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {COLORS["bg_tertiary"]};
    border: none;
    width: 20px;
}}

QSpinBox::up-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 5px solid {COLORS["text_secondary"]};
    width: 0; height: 0;
}}

QSpinBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS["text_secondary"]};
    width: 0; height: 0;
}}

/* ─── ComboBox ─── */
QComboBox {{
    background-color: {COLORS["bg_tertiary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS["text_primary"]};
    font-size: 13px;
    min-width: 120px;
}}

QComboBox:focus {{
    border-color: {COLORS["accent_blue"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS["text_secondary"]};
    width: 0; height: 0;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_tertiary"]};
    border: 1px solid {COLORS["border"]};
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent_blue"]};
    selection-color: white;
    border-radius: 4px;
    padding: 4px;
}}

/* ─── Buttons ─── */
QPushButton {{
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton#startButton {{
    background-color: {COLORS["accent_green"]};
    color: white;
    border: none;
}}

QPushButton#startButton:hover {{
    background-color: {COLORS["accent_green_hover"]};
}}

QPushButton#startButton:disabled {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_secondary"]};
}}

QPushButton#stopButton {{
    background-color: {COLORS["accent_red"]};
    color: white;
    border: none;
}}

QPushButton#stopButton:hover {{
    background-color: {COLORS["accent_red_hover"]};
}}

QPushButton#stopButton:disabled {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_secondary"]};
}}

QPushButton#browseButton {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["accent_blue"]};
    padding: 8px 14px;
    min-width: 30px;
}}

QPushButton#browseButton:hover {{
    background-color: {COLORS["border"]};
}}

QPushButton#clearButton {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border"]};
    padding: 8px 14px;
}}

QPushButton#clearButton:hover {{
    color: {COLORS["text_primary"]};
    border-color: {COLORS["text_secondary"]};
}}

/* ─── Progress Bar ─── */
QProgressBar {{
    background-color: {COLORS["bg_tertiary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    text-align: center;
    color: {COLORS["text_primary"]};
    font-size: 11px;
    min-height: 22px;
}}

QProgressBar::chunk {{
    background-color: {COLORS["accent_blue"]};
    border-radius: 5px;
}}

/* ─── Log Panel (QTextEdit) ─── */
QTextEdit#logPanel {{
    background-color: {COLORS["bg_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 12px;
    font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 12px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent_blue"]};
}}

/* ─── Scrollbar ─── */
QScrollBar:vertical {{
    background-color: {COLORS["bg_primary"]};
    width: 10px;
    border: none;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["border"]};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["text_secondary"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
"""


# ──────────────────────────────────────────────────
# Colores de log por severidad
# ──────────────────────────────────────────────────
LOG_COLORS = {
    "info": COLORS["text_primary"],
    "success": COLORS["accent_green"],
    "warn": COLORS["accent_orange"],
    "error": COLORS["accent_red"],
}


class MainWindow(QMainWindow):
    """
    Ventana principal de Paper Scout.
    
    Arquitectura MVC:
      - Esta clase es la Vista
      - PipelineWorker es el Controlador (ejecuta en QThread)
      - ArxivClient, LLMSummarizer, ObsidianWriter son el Modelo
    """

    def __init__(self):
        super().__init__()
        
        self._thread: Optional[QThread] = None
        self._worker: Optional[PipelineWorker] = None
        
        self._init_ui()
        self._load_saved_config()

    def _init_ui(self) -> None:
        """Construye toda la interfaz gráfica."""
        self.setWindowTitle("📚 Paper Scout — arXiv Paper Finder")
        self.setMinimumSize(720, 680)
        self.resize(780, 750)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(12)

        # ── Header ──
        header = QLabel("📚 Paper Scout")
        header.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {COLORS['accent_blue']}; "
            f"background: transparent; padding: 4px 0;"
        )
        subtitle = QLabel("Busca papers en arXiv, resúmelos con IA y guárdalos en Obsidian")
        subtitle.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_secondary']}; "
            f"background: transparent; margin-bottom: 4px;"
        )
        main_layout.addWidget(header)
        main_layout.addWidget(subtitle)

        # ── Sección: Búsqueda ──
        search_group = QGroupBox("🔍  Búsqueda")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)

        # Keywords
        kw_row = QHBoxLayout()
        kw_label = QLabel("Palabras clave:")
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText(
            "ej: transformer attention mechanism, reinforcement learning..."
        )
        self.keywords_input.setObjectName("keywordsInput")
        kw_row.addWidget(kw_label)
        kw_row.addWidget(self.keywords_input, 1)
        search_layout.addLayout(kw_row)

        # Max results
        max_row = QHBoxLayout()
        max_label = QLabel("Máx. resultados:")
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(1, 50)
        self.max_results_spin.setValue(10)
        self.max_results_spin.setObjectName("maxResultsSpin")
        max_row.addWidget(max_label)
        max_row.addWidget(self.max_results_spin)
        max_row.addStretch()
        search_layout.addLayout(max_row)

        main_layout.addWidget(search_group)

        # ── Sección: Configuración ──
        config_group = QGroupBox("⚙️  Configuración")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Vault path
        vault_row = QHBoxLayout()
        vault_label = QLabel("Vault de Obsidian:")
        self.vault_input = QLineEdit()
        self.vault_input.setPlaceholderText("/ruta/a/tu/vault/obsidian")
        self.vault_input.setObjectName("vaultInput")
        self.browse_btn = QPushButton("📁")
        self.browse_btn.setObjectName("browseButton")
        self.browse_btn.setToolTip("Seleccionar carpeta del vault")
        self.browse_btn.clicked.connect(self._browse_vault)
        vault_row.addWidget(vault_label)
        vault_row.addWidget(self.vault_input, 1)
        vault_row.addWidget(self.browse_btn)
        config_layout.addLayout(vault_row)

        # API Key + Provider
        api_row = QHBoxLayout()
        api_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Tu API key de Gemini o OpenAI")
        self.api_key_input.setObjectName("apiKeyInput")

        provider_label = QLabel("Proveedor:")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI", "Gemini", "Ollama (Local)"])
        self.provider_combo.setObjectName("providerCombo")
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)

        api_row.addWidget(api_label)
        api_row.addWidget(self.api_key_input, 1)
        api_row.addWidget(provider_label)
        api_row.addWidget(self.provider_combo)
        config_layout.addLayout(api_row)

        main_layout.addWidget(config_group)

        # ── Sección: Controles ──
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.start_btn = QPushButton("▶  Iniciar Búsqueda")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self._start_pipeline)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.stop_btn = QPushButton("⏹  Detener")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_pipeline)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.clear_btn = QPushButton("🗑  Limpiar Logs")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self._clear_logs)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.clear_btn)

        main_layout.addLayout(controls_layout)

        # ── Progress Bar ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Esperando...")
        main_layout.addWidget(self.progress_bar)

        # ── Log Panel ──
        log_group = QGroupBox("📋  Logs")
        log_layout = QVBoxLayout(log_group)

        self.log_panel = QTextEdit()
        self.log_panel.setObjectName("logPanel")
        self.log_panel.setReadOnly(True)
        self.log_panel.setMinimumHeight(180)
        self.log_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        log_layout.addWidget(self.log_panel)
        main_layout.addWidget(log_group, 1)  # strech=1 para que crezca

        # ── Footer ──
        footer = QLabel("Paper Scout v1.0 — Hecho con ❤️ para investigadores")
        footer.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_secondary']}; "
            f"background: transparent; padding: 4px 0;"
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

    # ──────────────────────────────────────────────
    # Acciones de la UI
    # ──────────────────────────────────────────────

    def _browse_vault(self) -> None:
        """Abre un diálogo para seleccionar la carpeta del vault."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Vault de Obsidian",
            self.vault_input.text() or str(
                __import__("pathlib").Path.home()
            ),
        )
        if path:
            self.vault_input.setText(path)

    def _clear_logs(self) -> None:
        """Limpia el panel de logs."""
        self.log_panel.clear()

    def _on_provider_changed(self, text: str) -> None:
        """Habilita o deshabilita el campo de API Key según el proveedor."""
        is_ollama = "Ollama" in text
        self.api_key_input.setEnabled(not is_ollama)
        if is_ollama:
            self.api_key_input.setPlaceholderText("No requerida para Ollama")
            self.api_key_input.setText("")
        else:
            self.api_key_input.setPlaceholderText("Tu API key de Gemini o OpenAI")

    def _validate_inputs(self) -> Optional[str]:
        """
        Valida todos los campos de entrada.
        
        Returns:
            None si es válido, string con el error si no.
        """
        if not self.keywords_input.text().strip():
            return "Debes ingresar al menos una palabra clave"
        if not self.vault_input.text().strip():
            return "Debes seleccionar la carpeta del vault de Obsidian"
        
        # API Key solo es obligatoria para Gemini y OpenAI
        provider = self.provider_combo.currentText().lower()
        if "ollama" not in provider and not self.api_key_input.text().strip():
            return "Debes ingresar tu API key para este proveedor"
        
        from pathlib import Path
        vault_path = Path(self.vault_input.text().strip())
        if not vault_path.exists():
            return f"La ruta del vault no existe: {vault_path}"
        
        return None

    # ──────────────────────────────────────────────
    # Pipeline Control (Worker Object Pattern)
    # ──────────────────────────────────────────────

    def _start_pipeline(self) -> None:
        """
        Inicia el pipeline en un hilo separado.
        
        Sigue estrictamente el Worker Object Pattern
        (skills/pyqt6-async/SKILL.md):
        1. Crear QThread
        2. Crear Worker(QObject) con config
        3. moveToThread
        4. Conectar señales
        5. thread.start()
        """
        # Validar inputs
        error = self._validate_inputs()
        if error:
            QMessageBox.warning(self, "Validación", error)
            return

        # Guardar configuración para la próxima sesión
        self._save_current_config()

        # Actualizar UI
        self._set_running_state(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Iniciando pipeline...")
        self._append_log("🚀 Iniciando pipeline...", "info")

        # Crear configuración del pipeline
        config = PipelineConfig(
            keywords=self.keywords_input.text().strip(),
            max_results=self.max_results_spin.value(),
            vault_path=self.vault_input.text().strip(),
            api_key=self.api_key_input.text().strip(),
            provider=self.provider_combo.currentText().split(" ")[0].lower(),
        )

        # ── Worker Object Pattern ──
        # Paso 1: Crear thread y worker
        self._thread = QThread()
        self._worker = PipelineWorker(config)

        # Paso 2: Mover worker al thread
        self._worker.moveToThread(self._thread)

        # Paso 3: Conectar señales
        self._thread.started.connect(self._worker.run)
        self._worker.log_signal.connect(self._append_log)
        self._worker.progress_signal.connect(self._update_progress)
        self._worker.finished_signal.connect(self._on_pipeline_finished)

        # Cleanup (skills/pyqt6-async/SKILL.md §2)
        self._worker.finished_signal.connect(self._thread.quit)
        self._worker.finished_signal.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # Paso 4: Iniciar thread
        self._thread.start()

    def _stop_pipeline(self) -> None:
        """Solicita la cancelación del pipeline activo."""
        if self._worker:
            self._worker.cancel()
            self._append_log("⏳ Solicitando cancelación...", "warn")
            self.stop_btn.setEnabled(False)

    def _set_running_state(self, running: bool) -> None:
        """Actualiza el estado visual de los controles."""
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.keywords_input.setEnabled(not running)
        self.vault_input.setEnabled(not running)
        self.api_key_input.setEnabled(not running)
        self.provider_combo.setEnabled(not running)
        self.max_results_spin.setEnabled(not running)
        self.browse_btn.setEnabled(not running)

    # ──────────────────────────────────────────────
    # Slots (reciben señales del worker)
    # ──────────────────────────────────────────────

    def _append_log(self, message: str, level: str = "info") -> None:
        """
        Añade un mensaje al panel de logs con color según severidad.
        
        Se ejecuta en el hilo principal (llamado vía signal/slot).
        """
        color = LOG_COLORS.get(level, COLORS["text_primary"])
        
        # Timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        html = (
            f'<span style="color: {COLORS["text_secondary"]};">[{timestamp}]</span> '
            f'<span style="color: {color};">{message}</span>'
        )
        self.log_panel.append(html)
        
        # Auto-scroll al final
        cursor = self.log_panel.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_panel.setTextCursor(cursor)

    def _update_progress(self, current: int, total: int) -> None:
        """Actualiza la barra de progreso."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"Procesando {current}/{total} papers ({percentage}%)")

    def _on_pipeline_finished(self, success: bool, message: str) -> None:
        """Maneja la finalización del pipeline."""
        self._set_running_state(False)

        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("✅ Completado")
        else:
            self.progress_bar.setFormat("❌ Error")
            # Mostrar mensaje de error en un diálogo si es crítico
            if "Cuota" in message:
                QMessageBox.warning(self, "Límite de API", message)

        # NOTA: No ponemos self._worker = None ni self._thread = None aquí.
        # El cleanup real ocurre vía signals (finished -> deleteLater).
        # Esto evita que el objeto C++ sea destruido mientras el hilo aún sale.

    # ──────────────────────────────────────────────
    # Config persistence
    # ──────────────────────────────────────────────

    def _load_saved_config(self) -> None:
        """Carga la configuración guardada de la sesión anterior."""
        config = load_config()
        
        if config.get("vault_path"):
            self.vault_input.setText(config["vault_path"])
        if config.get("keywords"):
            self.keywords_input.setText(config["keywords"])
        if config.get("max_results"):
            self.max_results_spin.setValue(config["max_results"])
        if config.get("provider"):
            provider = config["provider"].capitalize()
            index = self.provider_combo.findText(provider)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)

    def _save_current_config(self) -> None:
        """Guarda la configuración actual para la próxima sesión."""
        config = {
            "vault_path": self.vault_input.text().strip(),
            "keywords": self.keywords_input.text().strip(),
            "max_results": self.max_results_spin.value(),
            "provider": self.provider_combo.currentText().lower(),
        }
        save_config(config)

    # ──────────────────────────────────────────────
    # Closevent
    # ──────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """Guarda configuración y limpia hilos de forma segura al cerrar."""
        self._save_current_config()

        if self._thread and self._thread.isRunning():
            # Intentar cancelación elegante
            if self._worker:
                self._worker.cancel()
            
            # Detener el event loop del hilo
            self._thread.quit()
            
            # Esperar a que el hilo termine realmente. 
            # Si no termina en 2 segundos, forzamos (aunque terminate es agresivo,
            # es mejor que un core dump en el cierre).
            if not self._thread.wait(2000):
                self._thread.terminate()
                self._thread.wait()

        event.accept()
