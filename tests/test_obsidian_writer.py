import pytest
from datetime import datetime
from pathlib import Path
from src.models.arxiv_client import Paper
from src.models.obsidian_writer import ObsidianWriter, _sanitize_filename, _build_frontmatter

def test_sanitize_filename_matches_skill():
    """Verifica que la sanitización cumpla con SKILL.md."""
    input_title = "Attention Is All You Need: A Novel Architecture!"
    expected = "attention-is-all-you-need-a-novel-architecture"
    assert _sanitize_filename(input_title) == expected

def test_frontmatter_authors_as_wikilinks():
    """Verifica que los autores sean wikilinks [[Author]]."""
    paper = Paper(
        title="Test Paper",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        abstract="...",
        published=datetime(2017, 6, 12),
        updated=datetime(2017, 6, 12),
        arxiv_id="1706.03762",
        url="https://arxiv.org/abs/1706.03762",
        pdf_url="https://arxiv.org/pdf/1706.03762",
        categories=["cs.CL"]
    )
    frontmatter = _build_frontmatter(paper, ["paper", "nlp"])
    
    assert 'AUTHORS:' in frontmatter.upper()
    assert '[[Ashish Vaswani]]' in frontmatter
    assert '[[Noam Shazeer]]' in frontmatter
    assert 'aliases: []' in frontmatter
    assert 'arxiv_id: "1706.03762"' in frontmatter

def test_obsidian_writer_skip_duplicates(tmp_path):
    """Verifica que no se sobreescriban archivos existentes."""
    vault = tmp_path / "vault"
    vault.mkdir()
    
    writer = ObsidianWriter(str(vault))
    paper = Paper(
        title="Duplicate Paper",
        authors=["Author"],
        abstract="...",
        published=datetime(2024, 1, 1),
        updated=datetime(2024, 1, 1),
        arxiv_id="1234.5678",
        url="...",
        pdf_url="...",
        categories=["cs.AI"]
    )
    
    # Crear archivo manual
    filename = "2024-01-01_duplicate-paper.md"
    existing_file = vault / filename
    existing_file.write_text("Old Content")
    
    success, message = writer.write(paper, "New Summary")
    assert success is False
    assert "Archivo ya existe" in message
    assert existing_file.read_text() == "Old Content"
