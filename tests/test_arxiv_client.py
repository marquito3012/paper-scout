"""
Tests para ArxivClient.

Usa mocks para evitar llamadas reales a la API de arXiv.
Verifica el parsing correcto de resultados y manejo de errores.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.models.arxiv_client import ArxivClient, Paper


class MockAuthor:
    """Mock de arxiv.Result.Author."""
    def __init__(self, name: str):
        self.name = name


class MockResult:
    """Mock de arxiv.Result con todos los campos necesarios."""
    def __init__(
        self,
        title="Test Paper Title",
        authors=None,
        summary="This is a test abstract.",
        published=None,
        updated=None,
        entry_id="http://arxiv.org/abs/2401.12345v1",
        pdf_url="http://arxiv.org/pdf/2401.12345v1",
        categories=None,
    ):
        self.title = title
        self.authors = authors or [MockAuthor("Author A"), MockAuthor("Author B")]
        self.summary = summary
        self.published = published or datetime(2024, 1, 15)
        self.updated = updated or datetime(2024, 1, 16)
        self.entry_id = entry_id
        self.pdf_url = pdf_url
        self.categories = categories or ["cs.AI", "cs.LG"]


class TestArxivClient:
    """Tests para la clase ArxivClient."""

    @patch("src.models.arxiv_client.arxiv.Client")
    def test_search_returns_papers(self, mock_client_cls):
        """Verifica que search() devuelve una lista de Paper correctamente parseados."""
        # Arrange
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_results = [
            MockResult(
                title="Attention Is All You Need",
                authors=[MockAuthor("Vaswani"), MockAuthor("Shazeer")],
                summary="We propose a new architecture...",
                categories=["cs.CL", "cs.LG"],
            ),
            MockResult(
                title="BERT: Pre-training of Deep Bidirectional Transformers",
                authors=[MockAuthor("Devlin")],
                summary="We introduce BERT...",
                categories=["cs.CL"],
            ),
        ]
        mock_client.results.return_value = iter(mock_results)
        
        # Act
        client = ArxivClient()
        papers = client.search("transformer attention", max_results=5)
        
        # Assert
        assert len(papers) == 2
        assert isinstance(papers[0], Paper)
        assert papers[0].title == "Attention Is All You Need"
        assert papers[0].authors == ["Vaswani", "Shazeer"]
        assert papers[0].abstract == "We propose a new architecture..."
        assert papers[0].categories == ["cs.CL", "cs.LG"]
        assert "2401.12345" in papers[0].arxiv_id

    @patch("src.models.arxiv_client.arxiv.Client")
    def test_search_empty_results(self, mock_client_cls):
        """Verifica que search() devuelve lista vacía cuando no hay resultados."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.results.return_value = iter([])
        
        client = ArxivClient()
        papers = client.search("nonexistent_query_xyz")
        
        assert papers == []

    @patch("src.models.arxiv_client.arxiv.Client")
    def test_search_caps_max_results(self, mock_client_cls):
        """Verifica que max_results se limita a 50."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.results.return_value = iter([])
        
        client = ArxivClient()
        client.search("test", max_results=100)
        
        # Verificar que el Search se creó con max_results=50
        call_args = mock_client.results.call_args
        search_obj = call_args[0][0]
        assert search_obj.max_results == 50

    @patch("src.models.arxiv_client.arxiv.Client")
    def test_search_connection_error(self, mock_client_cls):
        """Verifica que los errores de red se envuelven en ConnectionError."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.results.side_effect = Exception("Network error")
        
        client = ArxivClient()
        
        with pytest.raises(ConnectionError, match="Error al buscar en arXiv"):
            client.search("test")
    def test_preprocess_query_logic(self):
        """Verifica la transformación de queries con comas (phrases)."""
        client = ArxivClient()
        
        # Caso 1: Sin comas (comportamiento original)
        assert client._preprocess_query("deep learning") == "deep learning"
        
        # Caso 2: Con comas (phrases)
        assert client._preprocess_query("deep learning, transformer") == '"deep learning" AND "transformer"'
        
        # Caso 3: Ya tiene comillas
        assert client._preprocess_query('"deep learning", transformer') == '"deep learning" AND "transformer"'
        
        # Caso 4: Espacios extra
        assert client._preprocess_query("  ai ,  nlp  ") == '"ai" AND "nlp"'
        
        # Caso 5: Query vacía
        assert client._preprocess_query("   ") == ""
