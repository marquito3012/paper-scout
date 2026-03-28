"""
Tests para ObsidianWriter.

Verifica:
  - Generación correcta de frontmatter YAML
  - Sanitización de nombres de archivo
  - Mapeo de categorías arXiv → tags
  - Manejo de archivos duplicados
  - Contenido completo de la nota generada
"""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path

from src.models.arxiv_client import Paper
from src.models.obsidian_writer import (
    ObsidianWriter,
    _sanitize_filename,
    _map_categories_to_tags,
    _build_frontmatter,
    ARXIV_CATEGORY_TAGS,
)


def _make_paper(**kwargs):
    """Helper para crear un Paper de prueba."""
    defaults = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        "published": datetime(2017, 6, 12),
        "updated": datetime(2017, 6, 12),
        "arxiv_id": "1706.03762",
        "url": "https://arxiv.org/abs/1706.03762",
        "pdf_url": "https://arxiv.org/pdf/1706.03762",
        "categories": ["cs.CL", "cs.LG"],
    }
    defaults.update(kwargs)
    return Paper(**defaults)


class TestSanitizeFilename:
    """Tests para la función _sanitize_filename."""

    def test_basic_sanitization(self):
        result = _sanitize_filename("Attention Is All You Need")
        assert result == "attention-is-all-you-need"

    def test_special_characters_removed(self):
        result = _sanitize_filename("A Novel Architecture: Theory & Practice (2024)")
        assert ":" not in result
        assert "&" not in result
        assert "(" not in result
        assert ")" not in result

    def test_multiple_hyphens_collapsed(self):
        result = _sanitize_filename("Test --- Paper --- Title")
        assert "---" not in result

    def test_truncation_at_80_chars(self):
        long_title = "A " * 100  # 200 chars
        result = _sanitize_filename(long_title)
        assert len(result) <= 80

    def test_no_leading_trailing_hyphens(self):
        result = _sanitize_filename("---Test Title---")
        assert not result.startswith("-")
        assert not result.endswith("-")


class TestMapCategoriesToTags:
    """Tests para la función _map_categories_to_tags."""

    def test_always_includes_paper_tag(self):
        tags = _map_categories_to_tags([])
        assert "paper" in tags
        assert tags[0] == "paper"

    def test_known_categories_mapped(self):
        tags = _map_categories_to_tags(["cs.AI", "cs.CL"])
        assert "artificial-intelligence" in tags
        assert "nlp" in tags

    def test_unknown_category_slugified(self):
        tags = _map_categories_to_tags(["cs.XX"])
        assert "cs-xx" in tags

    def test_no_duplicate_tags(self):
        # cs.LG and stat.ML both map to "machine-learning"
        tags = _map_categories_to_tags(["cs.LG", "stat.ML"])
        assert tags.count("machine-learning") == 1


class TestBuildFrontmatter:
    """Tests para la función _build_frontmatter."""

    def test_contains_required_fields(self):
        paper = _make_paper()
        tags = ["paper", "nlp"]
        fm = _build_frontmatter(paper, tags)

        assert 'title: "Attention Is All You Need"' in fm
        assert "Ashish Vaswani" in fm
        assert "Noam Shazeer" in fm
        assert "- paper" in fm
        assert "- nlp" in fm
        assert "date: 2017-06-12" in fm
        assert 'arxiv_id: "1706.03762"' in fm
        assert "status: unread" in fm

    def test_escapes_quotes_in_title(self):
        paper = _make_paper(title='Paper with "quotes" inside')
        tags = ["paper"]
        fm = _build_frontmatter(paper, tags)
        assert '\\"quotes\\"' in fm

    def test_starts_and_ends_with_delimiters(self):
        paper = _make_paper()
        fm = _build_frontmatter(paper, ["paper"])
        assert fm.startswith("---")
        assert fm.endswith("---")


class TestObsidianWriter:
    """Tests para la clase ObsidianWriter."""

    def test_invalid_vault_path_raises(self):
        with pytest.raises(FileNotFoundError):
            ObsidianWriter("/nonexistent/path/to/vault")

    def test_write_creates_file(self):
        """Verifica que write() crea un archivo .md con el contenido correcto."""
        paper = _make_paper()
        summary = "## 🎯 Objetivo Principal\nTest summary content"

        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ObsidianWriter(tmpdir)
            success, filepath = writer.write(paper, summary)

            assert success is True
            assert filepath.endswith(".md")

            # Verificar que el archivo existe
            assert Path(filepath).exists()

            # Verificar contenido
            content = Path(filepath).read_text(encoding="utf-8")
            assert "---" in content  # Frontmatter delimiters
            assert "Attention Is All You Need" in content
            assert "Test summary content" in content
            assert "paper-scout" in content  # Footer attribution

    def test_write_skips_duplicate(self):
        """Verifica que archivos duplicados se saltan sin error."""
        paper = _make_paper()
        summary = "Test summary"

        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ObsidianWriter(tmpdir)

            # Primera escritura
            success1, _ = writer.write(paper, summary)
            assert success1 is True

            # Segunda escritura (duplicado)
            success2, message = writer.write(paper, summary)
            assert success2 is False
            assert "ya existe" in message

    def test_filename_format(self):
        """Verifica el formato YYYY-MM-DD_titulo-sanitizado.md."""
        paper = _make_paper(
            title="Test Paper Title",
            published=datetime(2024, 3, 15),
        )
        summary = "Summary"

        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ObsidianWriter(tmpdir)
            success, filepath = writer.write(paper, summary)

            filename = Path(filepath).name
            assert filename.startswith("2024-03-15_")
            assert filename.endswith(".md")
            assert "test-paper-title" in filename
