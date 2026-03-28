"""
pipeline_controller.py — Controlador del pipeline con Worker Object Pattern.

Implementa el patrón Worker Object (QObject + QThread) siguiendo las reglas
estrictas definidas en skills/pyqt6-async/SKILL.md:
  - Worker hereda de QObject, NUNCA de QThread
  - Toda comunicación worker→UI es vía pyqtSignal
  - Cancelación segura con threading.Event
  - Cleanup automático con deleteLater
"""

import threading
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.models.arxiv_client import ArxivClient, Paper
from src.models.llm_summarizer import LLMSummarizer
from src.models.obsidian_writer import ObsidianWriter
from src.utils.notifier import notify


@dataclass
class PipelineConfig:
    """Configuración inmutable del pipeline."""
    keywords: str
    max_results: int
    vault_path: str
    api_key: str
    provider: str  # "gemini" o "openai"
    use_gpu: bool


class PipelineWorker(QObject):
    """
    Worker que ejecuta el pipeline completo en un hilo separado.
    
    Pipeline: arXiv search → LLM summarize → Obsidian write → desktop notify
    
    Señales emitidas (thread-safe, procesadas en el event loop del hilo principal):
      - log_signal(str, str): (mensaje, nivel) para el panel de logs
      - progress_signal(int, int): (actual, total) para la barra de progreso
      - finished_signal(bool, str): (éxito, mensaje) al finalizar
    
    IMPORTANTE: Este worker NUNCA accede a widgets de Qt directamente.
    Toda comunicación con la UI se hace exclusivamente vía señales.
    """

    # ── Señales para comunicación thread-safe con la UI ──
    log_signal = pyqtSignal(str, str)        # (mensaje, nivel: info|warn|error|success)
    progress_signal = pyqtSignal(int, int)   # (current_step, total_steps)
    finished_signal = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, config: PipelineConfig):
        super().__init__()
        self._config = config
        # Flag de cancelación thread-safe (skills/pyqt6-async/SKILL.md §4)
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """
        Solicita la cancelación del pipeline.
        
        Llamado desde el hilo principal. El worker revisa este flag
        entre cada paso del pipeline para detenerse limpiamente.
        """
        self._cancel_event.set()

    def _is_cancelled(self) -> bool:
        """Verifica si se solicitó cancelación."""
        return self._cancel_event.is_set()

    @pyqtSlot()
    def run(self) -> None:
        """
        Ejecuta el pipeline completo.
        
        Flujo:
        1. Buscar papers en arXiv con las palabras clave
        2. Por cada paper:
           a. Verificar cancelación
           b. Generar resumen con el LLM
           c. Guardar nota en Obsidian
           d. Actualizar progreso
        3. Enviar notificación de escritorio
        4. Emitir señal de finalización
        
        Todos los errores se capturan y se emiten como log_signal(error).
        El pipeline continúa al siguiente paper si uno falla.
        """
        saved_count = 0
        skipped_count = 0
        error_count = 0

        try:
            # ── Paso 1: Búsqueda en arXiv ──
            self.log_signal.emit(
                f"🔍 Buscando papers: '{self._config.keywords}' "
                f"(máx: {self._config.max_results})",
                "info"
            )

            arxiv_client = ArxivClient()
            papers = arxiv_client.search(
                query=self._config.keywords,
                max_results=self._config.max_results,
            )

            if not papers:
                self.log_signal.emit(
                    "⚠️ No se encontraron papers para esas palabras clave",
                    "warn"
                )
                self.finished_signal.emit(True, "No se encontraron papers")
                return

            self.log_signal.emit(
                f"📄 Encontrados {len(papers)} papers",
                "success"
            )

            # ── Paso 2: Inicializar LLM ──
            self.log_signal.emit(
                f"🤖 Inicializando {self._config.provider.upper()}...",
                "info"
            )
            summarizer = LLMSummarizer(
                provider=self._config.provider,
                api_key=self._config.api_key,
                use_gpu=self._config.use_gpu,
            )

            # ── Paso 3: Inicializar escritor de Obsidian ──
            writer = ObsidianWriter(vault_path=self._config.vault_path)

            total = len(papers)

            # ── Paso 4: Procesar cada paper ──
            for i, paper in enumerate(papers):
                # Verificar cancelación entre cada paper
                if self._is_cancelled():
                    self.log_signal.emit(
                        "⛔ Pipeline cancelado por el usuario",
                        "warn"
                    )
                    break

                self.progress_signal.emit(i, total)
                self.log_signal.emit(
                    f"📝 [{i + 1}/{total}] Procesando: {paper.title[:80]}...",
                    "info"
                )

                # ── 4a: Generar resumen ──
                try:
                    summary = summarizer.summarize(paper)
                except Exception as e:
                    self.log_signal.emit(
                        f"❌ Error al resumir '{paper.title[:50]}': {str(e)}",
                        "error"
                    )
                    error_count += 1
                    continue

                # Verificar cancelación después del resumen (puede tardar)
                if self._is_cancelled():
                    self.log_signal.emit(
                        "⛔ Pipeline cancelado por el usuario",
                        "warn"
                    )
                    break

                # ── 4b: Guardar nota ──
                try:
                    success, message = writer.write(paper, summary)
                    if success:
                        self.log_signal.emit(
                            f"✅ Guardado: {message.split('/')[-1]}",
                            "success"
                        )
                        saved_count += 1
                    else:
                        self.log_signal.emit(
                            f"⏭️ {message}",
                            "warn"
                        )
                        skipped_count += 1
                except Exception as e:
                    self.log_signal.emit(
                        f"❌ Error al guardar '{paper.title[:50]}': {str(e)}",
                        "error"
                    )
                    error_count += 1

            # ── Paso 5: Actualizar progreso final ──
            self.progress_signal.emit(total, total)

            # ── Paso 6: Notificación de escritorio ──
            result_msg = (
                f"✅ Completado: {saved_count} guardados, "
                f"{skipped_count} saltados, {error_count} errores"
            )
            self.log_signal.emit(result_msg, "success")

            notify(
                title="Paper Scout — Completado",
                message=f"{saved_count} papers guardados en Obsidian",
                icon="dialog-information",
            )

            self.finished_signal.emit(True, result_msg)

        except ConnectionError as e:
            error_msg = f"❌ Error de conexión: {str(e)}"
            self.log_signal.emit(error_msg, "error")
            self.finished_signal.emit(False, error_msg)

        except Exception as e:
            error_msg = f"❌ Error inesperado: {str(e)}"
            self.log_signal.emit(error_msg, "error")
            self.finished_signal.emit(False, error_msg)
