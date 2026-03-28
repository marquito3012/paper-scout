from PyQt6.QtCore import QObject, pyqtSignal
from src.models.llm_summarizer import LLMSummarizer

class KeywordWorker(QObject):
    """
    Worker que genera palabras clave optimizadas via LLM de forma asíncrona.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, provider: str, api_key: str, description: str, use_gpu: bool = False):
        super().__init__()
        self.provider = provider
        self.api_key = api_key
        self.description = description
        self.use_gpu = use_gpu

    def run(self):
        """Ejecuta la generación en el hilo secundario."""
        try:
            summarizer = LLMSummarizer(self.provider, self.api_key, self.use_gpu)
            keywords = summarizer.generate_keywords(self.description)
            self.finished.emit(keywords)
        except Exception as e:
            self.error.emit(str(e))
