---
name: Obsidian Markdown Generation
description: Estructura exacta del archivo .md que se genera para Obsidian, incluyendo frontmatter YAML obligatorio, formato del resumen y convenciones de nombrado.
---

# Obsidian Markdown Generation — Especificación

## 1. Estructura del Archivo (OBLIGATORIA)

Todo archivo `.md` generado por paper-scout DEBE seguir esta estructura exacta:

---
title: "Título completo del paper"
aliases: 
  - "Acrónimo o nombre corto si lo tiene (ej. BERT, GPT-4)"
authors:
  - "[[Nombre Autor 1]]"
  - "[[Nombre Autor 2]]"
tags:
  - paper
  - [categoria_arxiv_mapeada]
date: YYYY-MM-DD
arxiv_id: "XXXX.XXXXX"
url: "https://arxiv.org/abs/XXXX.XXXXX"
pdf_url: "https://arxiv.org/pdf/XXXX.XXXXX"
categories:
  - cs.AI
status: unread
created: YYYY-MM-DD
---

# Título completo del paper

> **Abstract:** Texto completo del abstract original en inglés...

---

## 🎯 Objetivo Principal
[Resumen generado por IA en español]

## 🔬 Metodología
[Resumen generado por IA en español. *Instrucción para el LLM: Envuelve arquitecturas, algoritmos o frameworks clave en wikilinks, ej. [[Transformer]], [[PyTorch]]*]

## 📊 Resultados Clave
[Resumen generado por IA en español]

## 💡 Contribución e Impacto
[Resumen generado por IA en español]

## 🔗 Conceptos Clave y Conexiones
* **Conceptos:** [[Concepto Clave 1]], [[Concepto Clave 2]], [[Concepto Clave 3]]
* **Relación con el estado del arte:** [Explicación generada por IA sobre cómo este paper avanza el campo, mencionando otros paradigmas entre corchetes si es relevante].

---

*Nota generada automáticamente por [paper-scout](https://github.com/marquito3012/paper-scout)*

---

## 2. Frontmatter YAML — Campos Obligatorios

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `title` | string (quoted) | Título completo del paper | `"Attention Is All You Need"` |
| `authors` | list[string] | Lista de autores | `- Ashish Vaswani` |
| `tags` | list[string] | SIEMPRE incluir `paper` + tags mapeados de categorías | `- paper\n- transformer` |
| `date` | date | Fecha de publicación original (ISO 8601) | `2017-06-12` |
| `arxiv_id` | string (quoted) | ID del paper en arXiv | `"1706.03762"` |
| `url` | string (quoted) | URL del abstract | `"https://arxiv.org/abs/1706.03762"` |
| `pdf_url` | string (quoted) | URL del PDF | `"https://arxiv.org/pdf/1706.03762"` |
| `categories` | list[string] | Categorías originales de arXiv | `- cs.CL` |
| `status` | string | Estado de lectura, siempre `unread` al crear | `unread` |
| `created` | date | Fecha de creación de la nota (hoy) | `2026-03-28` |

## 3. Mapeo de Categorías arXiv → Tags

```python
ARXIV_CATEGORY_TAGS = {
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
```

Si una categoría no está en el mapeo, usar la categoría original limpia (ej. `cs.PL` → `cs-pl`).

## 4. Convenciones de Nombrado de Archivo

### Formato: `YYYY-MM-DD_titulo-sanitizado.md`

### Reglas de sanitización:
1. Convertir a minúsculas
2. Reemplazar espacios con guiones (`-`)
3. Eliminar caracteres especiales: `[ ] ( ) { } : ; " ' , . ! ? @ # $ % ^ & * + = / \\ | < > ~`
4. Colapsar guiones múltiples en uno solo
5. Truncar a máximo 80 caracteres (sin cortar palabras)
6. Eliminar guiones al inicio/final

### Ejemplo:
- Input: `"Attention Is All You Need: A Novel Architecture"`
- Output: `2017-06-12_attention-is-all-you-need-a-novel-architecture.md`

## 5. Manejo de Duplicados

Si el archivo ya existe en la ruta de destino:
- **NO sobreescribir**
- Emitir un log de nivel `warn`: `"Archivo ya existe, saltando: {filename}"`
- Continuar con el siguiente paper

## 6. Encoding

- Todos los archivos se escriben en **UTF-8** sin BOM
- Saltos de línea: **LF** (`\n`), nunca CRLF
