"""
Tests para LLMSummarizer.

Usa mocks para evitar llamadas reales a las APIs de Gemini/OpenAI.
Verifica la inicialización correcta, construcción de prompts y manejo de errores.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.models.arxiv_client import Paper
from src.models.llm_summarizer import LLMSummarizer, SYSTEM_PROMPT, _build_user_prompt


def _make_paper(**kwargs):
    """Helper para crear un Paper de prueba."""
    defaults = {
        "title": "Test Paper",
        "authors": ["Author A"],
        "abstract": "This is a test abstract about machine learning.",
        "published": datetime(2024, 1, 15),
        "updated": datetime(2024, 1, 16),
        "arxiv_id": "2401.12345",
        "url": "https://arxiv.org/abs/2401.12345",
        "pdf_url": "https://arxiv.org/pdf/2401.12345",
        "categories": ["cs.AI"],
    }
    defaults.update(kwargs)
    return Paper(**defaults)


class TestBuildUserPrompt:
    """Tests para la función _build_user_prompt."""

    def test_contains_title(self):
        paper = _make_paper(title="My Great Paper")
        prompt = _build_user_prompt(paper)
        assert "My Great Paper" in prompt

    def test_contains_abstract(self):
        paper = _make_paper(abstract="Novel approach to NLP...")
        prompt = _build_user_prompt(paper)
        assert "Novel approach to NLP..." in prompt

    def test_instructs_spanish(self):
        paper = _make_paper()
        prompt = _build_user_prompt(paper)
        assert "español" in prompt.lower()


class TestLLMSummarizer:
    """Tests para la clase LLMSummarizer."""

    def test_invalid_provider_raises(self):
        """Proveedor no soportado debe lanzar ValueError."""
        with pytest.raises(ValueError, match="no soportado"):
            LLMSummarizer(provider="anthropic", api_key="test")

    @patch("src.models.llm_summarizer.genai", create=True)
    def test_gemini_initialization(self, mock_genai):
        """Verifica que Gemini se inicializa con el Cliente de GenAI."""
        with patch.dict("sys.modules", {"google.genai": mock_genai}):
            summarizer = LLMSummarizer(provider="gemini", api_key="test-key")
            
            # El Cliente se inicializa con la API key
            mock_genai.Client.assert_called_once_with(api_key="test-key")

    @patch("src.models.llm_summarizer.ollama", create=True)
    def test_summarize_ollama_calls_chat(self, mock_ollama_module):
        """Verifica que la llamada a summarize para Ollama use el método chat."""
        with patch.dict("sys.modules", {"ollama": mock_ollama_module}):
            # Mock de la respuesta de Ollama
            mock_ollama_module.chat.return_value = {
                'message': {'content': 'Resumen local de Ollama'}
            }
            
            summarizer = LLMSummarizer(provider="ollama", api_key="")
            paper = _make_paper()
            
            result = summarizer.summarize(paper)
            
            assert result == "Resumen local de Ollama"
            mock_ollama_module.chat.assert_called_once()
            # Verificar que se usó el modelo llama3.2
            args, kwargs = mock_ollama_module.chat.call_args
            assert kwargs["model"] == "llama3.2"

    def test_system_prompt_has_required_sections(self):
        """Verifica que el system prompt tiene todas las secciones requeridas."""
        required_sections = [
            "Objetivo Principal",
            "Metodología",
            "Resultados Clave",
            "Contribución e Impacto",
            "Conexiones",
        ]
        for section in required_sections:
            assert section in SYSTEM_PROMPT, f"Falta sección: {section}"

    def test_system_prompt_instructs_spanish(self):
        """Verifica que el system prompt pide resúmenes en español."""
        assert "español" in SYSTEM_PROMPT.lower()
