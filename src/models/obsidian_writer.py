"""
obsidian_writer.py — Generador de notas Markdown para Obsidian.

Genera archivos .md con frontmatter YAML obligatorio siguiendo la especificación
definida en skills/obsidian-markdown/SKILL.md:
  - Frontmatter con título, autores, tags, fecha, arxiv_id, URLs, categorías, status
  - Abstract original en blockquote
  - Resumen generado por IA con secciones estructuradas
  - Footer con atribución

Convenciones de nombrado: YYYY-MM-DD_titulo-sanitizado.md
Encoding: UTF-8, saltos de línea LF.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.arxiv_client import Paper


# ──────────────────────────────────────────────────
# Mapeo de categorías arXiv → tags legibles para Obsidian
# ──────────────────────────────────────────────────
ARXIV_CATEGORY_TAGS: dict[str, str] = {
    # Computer Science
    "cs.AI": "artificial-intelligence",
    "cs.CL": "nlp",
    "cs.CV": "computer-vision",
    "cs.LG": "machine-learning",
    "cs.NE": "neural-networks",
    "cs.RO": "robotics",
    "cs.IR": "information-retrieval",
    "cs.CR": "cybersecurity",
    "cs.DC": "distributed-computing",
    "cs.SE": "software-engineering",
    # Statistics / Math
    "stat.ML": "machine-learning",
    "stat.TH": "statistics",
    "math.OC": "optimization",
    # Physics
    "quant-ph": "quantum-computing",
    # Electrical Engineering
    "eess.SP": "signal-processing",
    "eess.AS": "audio-speech",
}


def _sanitize_filename(title: str) -> str:
    """
    Sanitiza un título de paper para usarlo como nombre de archivo.
    
    Reglas (definidas en skills/obsidian-markdown/SKILL.md):
    1. Convertir a minúsculas
    2. Reemplazar espacios con guiones (-)
    3. Eliminar caracteres especiales específicos
    4. Colapsar guiones múltiples en uno solo
    5. Truncar a máximo 80 caracteres (sin cortar palabras)
    6. Eliminar guiones al inicio/final
    """
    # Paso 1: minúsculas
    name = title.lower()
    
    # Paso 2: espacios → guiones
    name = name.replace(" ", "-")
    
    # Paso 3: eliminar caracteres especiales listados en SKILL.md
    chars_to_remove = r'[\[\]\(\)\{\}\:\;\"\'\,\.\!\?\@\#\$\%\^\&\*\+\=\/\\\|\<\>\~]'
    name = re.sub(chars_to_remove, '', name)
    
    # Paso 4: colapsar guiones múltiples
    name = re.sub(r'-+', '-', name)
    
    # Paso 5: truncar a 80 chars sin cortar palabras
    if len(name) > 80:
        name = name[:80]
        # No cortar a mitad de "palabra" (segmento entre guiones)
        last_hyphen = name.rfind('-')
        if last_hyphen > 40:  # Solo si no perdemos demasiado
            name = name[:last_hyphen]
    
    # Paso 6: eliminar guiones al inicio/final
    name = name.strip('-')
    
    return name


def _map_categories_to_tags(categories: list[str]) -> list[str]:
    """
    Mapea categorías de arXiv a tags legibles para Obsidian.
    """
    tags = ["paper"]
    seen = {"paper"}
    
    for cat in categories:
        tag = ARXIV_CATEGORY_TAGS.get(cat, cat.lower().replace(".", "-"))
        if tag not in seen:
            tags.append(tag)
            seen.add(tag)
    
    return tags


def _build_frontmatter(paper: Paper, tags: list[str]) -> str:
    """
    Genera el bloque de frontmatter YAML para la nota de Obsidian.
    
    Reglas SKILL.md:
    - title, arxiv_id, url y pdf_url entre comillas dobles.
    - authors como wikilinks [[Autor]].
    - aliases vacío por defecto.
    """
    # Escapar comillas en el título para el YAML
    safe_title = paper.title.replace('"', '\\"')
    
    # Autores como wikilinks: [[Autor]]
    authors_yaml = "\n".join(f'  - "[[{author}]]"' for author in paper.authors)
    
    # Formatear tags y categorías
    tags_yaml = "\n".join(f"  - {tag}" for tag in tags)
    categories_yaml = "\n".join(f"  - {cat}" for cat in paper.categories)
    
    frontmatter = f"""---
title: "{safe_title}"
aliases: []
authors:
{authors_yaml}
tags:
{tags_yaml}
date: {paper.published.strftime('%Y-%m-%d')}
arxiv_id: "{paper.arxiv_id}"
url: "{paper.url}"
pdf_url: "{paper.pdf_url}"
categories:
{categories_yaml}
status: unread
created: {datetime.now().strftime('%Y-%m-%d')}
---"""
    
    return frontmatter


def _build_note_content(paper: Paper, summary: str, tags: list[str]) -> str:
    """
    Construye el contenido completo de la nota Markdown.
    
    Estructura:
    1. Frontmatter YAML
    2. Título como H1
    3. Abstract original en blockquote
    4. Resumen generado por IA (ya formateado con secciones)
    5. Footer con atribución
    """
    frontmatter = _build_frontmatter(paper, tags)
    
    # Formatear abstract como blockquote (cada línea con >)
    abstract_lines = paper.abstract.replace('\n', ' ').strip()
    
    content = f"""{frontmatter}

# {paper.title}

> **Abstract:** {abstract_lines}

---

{summary}

---

*Nota generada automáticamente por [paper-scout](https://github.com/marquito3012/paper-scout)*
"""
    
    return content


class ObsidianWriter:
    """
    Escritor de notas Markdown para Obsidian.
    
    Genera archivos .md en la ruta del vault especificada,
    con frontmatter YAML y resúmenes estructurados.
    """

    def __init__(self, vault_path: str):
        """
        Args:
            vault_path: Ruta absoluta a la carpeta del vault de Obsidian
                       donde se guardarán las notas.
        
        Raises:
            FileNotFoundError: Si la ruta del vault no existe.
        """
        self._vault_path = Path(vault_path)
        
        if not self._vault_path.exists():
            raise FileNotFoundError(
                f"La ruta del vault no existe: {vault_path}"
            )

    def write(self, paper: Paper, summary: str) -> tuple[bool, str]:
        """
        Genera y guarda una nota de Obsidian para un paper.

        Args:
            paper: Objeto Paper con los metadatos del paper.
            summary: Resumen generado por el LLM (texto Markdown).

        Returns:
            Tupla (success: bool, message: str).
            - (True, filepath) si se creó la nota exitosamente.
            - (False, reason) si se saltó (duplicado) o hubo error.
        """
        # Generar tags desde categorías
        tags = _map_categories_to_tags(paper.categories)
        
        # Generar nombre de archivo
        sanitized_title = _sanitize_filename(paper.title)
        date_prefix = paper.published.strftime("%Y-%m-%d")
        filename = f"{date_prefix}_{sanitized_title}.md"
        filepath = self._vault_path / filename
        
        # Verificar duplicados
        if filepath.exists():
            return (False, f"Archivo ya existe, saltando: {filename}")
        
        # Construir contenido
        content = _build_note_content(paper, summary, tags)
        
        # Escribir archivo (UTF-8, LF)
        try:
            filepath.write_text(content, encoding="utf-8")
            return (True, str(filepath))
        except OSError as e:
            return (False, f"Error al escribir archivo: {str(e)}")
