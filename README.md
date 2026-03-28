# 📚 Paper Scout

App de escritorio Linux con interfaz gráfica que busca papers de arXiv, los resume con IA y los guarda automáticamente como notas de Obsidian según tus palabras clave.

![Paper Scout GUI](assets/screenshot_gui.png)

## ✨ Características

- 🔍 **Búsqueda en arXiv** — Busca papers por palabras clave con la API oficial de arXiv
- 🤖 **Resúmenes con IA** — Genera resúmenes estructurados en español con Gemini o OpenAI
- 📝 **Notas de Obsidian** — Guarda automáticamente archivos `.md` con frontmatter YAML completo
- 🏷️ **Tags automáticos** — Mapea categorías de arXiv a tags legibles (ej. `cs.CL` → `nlp`)
- 🔔 **Notificaciones** — Avisa al terminar con `notify-send` en Linux
- 💾 **Persistencia** — Recuerda tu configuración entre sesiones
- 🧵 **Non-blocking UI** — Pipeline en segundo plano con `QThread` (Worker Object Pattern)

## 🚀 Instalación

### 1. Clonar y configurar entorno
```bash
# Clonar el repositorio
git clone https://github.com/marquito3012/paper-scout.git
cd paper-scout

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar el LLM (Elige una opción)

#### Opción A: Local con Ollama (Ilimitado y Privado) 🏠
Ideal si quieres evitar límites de cuota y procesar todo en tu CPU.
1.  **Instalar Ollama:** 
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
2.  **Descargar modelo recomendado:**
    Para un portátil estándar (sin GPU dedicada), se recomienda **Llama 3.2 (3B)** o **Phi-3 Mini**:
    ```bash
    ollama pull llama3.2
    ```
3.  **Asegurar que Ollama está corriendo:** La app se conectará automáticamente al servidor local (`localhost:11434`).

#### Opción B: Cloud con Gemini o OpenAI 🤖
1.  Obtén tu API Key desde [Google AI Studio](https://aistudio.google.com/) o [OpenAI Dashboard](https://platform.openai.com/).
2.  La App soporta **Gemini 2.0 Flash** y **GPT-4o mini** por defecto para máximo ahorro y velocidad.

---

## 🎮 Uso

1. **Lanzar la aplicación:**
   ```bash
   source .venv/bin/activate
   python main.py
   ```
2. **Configurar búsqueda:**
   - Introduce **palabras clave** (ej. `quantum computing error correction`).
   - Define el **máximo de resultados**.
3. **Configurar destino e IA:**
   - Selecciona tu **Vault de Obsidian** 📁.
   - Elige el **Proveedor** (Ollama, Gemini o OpenAI).
   - Si usas Cloud, pega tu **API Key**.
4. **▶ Iniciar Búsqueda:** La app buscará, resumirá y guardará los archivos `.md` de forma asíncrona.

Los archivos se guardarán con el formato: `YYYY-MM-DD_titulo-sanitizado.md`

## 📋 Formato de las Notas

Cada nota en Obsidian incluye un frontmatter YAML completo para facilitar el filtrado:

```yaml
---
title: "Título del paper"
authors: [Autor 1, Autor 2]
tags: [paper, nlp, machine-learning]
date: 2024-01-15
arxiv_id: "2401.12345"
url: "https://arxiv.org/abs/2401.12345"
pdf_url: "https://arxiv.org/pdf/2401.12345"
categories: [cs.CL, cs.AI]
status: unread
created: 2026-03-28
---
```

## 🧪 Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## 🏗️ Arquitectura (MVC)
- **Model:** Clientes de API, Generador de Markdown, Config Manager.
- **View:** Interfaz PyQt6 con QSS (Dark Theme).
- **Controller:** PipelineWorker gestionado por QThread para mantener la UI reactiva.

## 📄 Licencia
MIT
