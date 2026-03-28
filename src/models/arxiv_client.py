"""
arxiv_client.py — Cliente para la API de arXiv.

Usa la librería oficial `arxiv` para buscar papers por palabras clave.
La librería gestiona internamente el rate limiting (3s entre requests)
según las políticas de arXiv.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import arxiv


@dataclass
class Paper:
    """
    Dataclass inmutable que representa un paper de arXiv.
    
    Contiene todos los metadatos necesarios para generar la nota
    de Obsidian: título, autores, abstract, fechas, URLs y categorías.
    """
    title: str
    authors: list[str]
    abstract: str
    published: datetime
    updated: datetime
    arxiv_id: str
    url: str
    pdf_url: str
    categories: list[str] = field(default_factory=list)


class ArxivClient:
    """
    Cliente que encapsula las búsquedas en arXiv.
    
    Utiliza arxiv.Search con sort_by=SubmittedDate (descendente)
    para obtener los papers más recientes primero.
    """

    def __init__(self, page_size: int = 10):
        """
        Args:
            page_size: Número de resultados por página para la paginación
                       interna de la librería arxiv. Default: 10.
        """
        # arxiv.Client maneja el rate limiting internamente (3s delay)
        self._client = arxiv.Client(page_size=page_size)

    def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """
        Busca papers en arXiv por palabras clave.

        La query se envía directamente al campo `search_query` de la API.
        Soporta prefijos de campo como:
          - ti: (título)
          - au: (autor)
          - abs: (abstract)
          - cat: (categoría)
        
        Si la query es texto plano sin prefijos, busca en todos los campos.

        Args:
            query: Palabras clave o query estructurada de arXiv.
            max_results: Número máximo de resultados a retornar (1-50).

        Returns:
            Lista de objetos Paper con los metadatos de cada paper encontrado.

        Raises:
            ConnectionError: Si no hay conexión a internet.
            arxiv.HTTPError: Si la API de arXiv responde con error.
        """
        search = arxiv.Search(
            query=query,
            max_results=min(max_results, 50),  # Cap a 50 para ser responsable
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        papers: list[Paper] = []

        try:
            for result in self._client.results(search):
                paper = Paper(
                    title=result.title.strip(),
                    authors=[author.name for author in result.authors],
                    abstract=result.summary.strip(),
                    published=result.published,
                    updated=result.updated,
                    arxiv_id=result.entry_id.split("/abs/")[-1],
                    url=result.entry_id,
                    pdf_url=result.pdf_url or "",
                    categories=result.categories,
                )
                papers.append(paper)

        except Exception as e:
            # Re-raise con contexto para el worker
            raise ConnectionError(
                f"Error al buscar en arXiv: {str(e)}"
            ) from e

        return papers
