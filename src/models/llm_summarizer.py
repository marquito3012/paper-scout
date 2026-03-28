"""
llm_summarizer.py — Orquestador de LLM para generación de resúmenes.

Soporta dos proveedores:
  - Google Gemini (google-generativeai) → modelo: gemini-2.0-flash
  - OpenAI (openai) → modelo: gpt-4o-mini

El prompt está diseñado para generar resúmenes estructurados en español
con secciones predefinidas que se integran directamente en las notas de Obsidian.
"""

from typing import Optional

from src.models.arxiv_client import Paper


# ──────────────────────────────────────────────────
# System prompt optimizado para resúmenes académicos
# ──────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un asistente experto en investigación académica. Dado el título y el abstract de un paper de arXiv, genera un resumen estructurado en español con las siguientes secciones exactas:

## 🎯 Objetivo Principal
[1-2 oraciones sobre el objetivo principal del paper]

## 🔬 Metodología
[2-3 oraciones sobre el enfoque/método utilizado]

## 📊 Resultados Clave
[Lista con viñetas de los hallazgos principales]

## 💡 Contribución e Impacto
[1-2 oraciones sobre por qué este paper es relevante]

## 🔗 Conexiones
[Sugiere temas o campos relacionados para lectura adicional]

REGLAS:
- Escribe siempre en español.
- Sé conciso pero informativo.
- Usa terminología técnica apropiada.
- No inventes datos que no estén en el abstract.
- Mantén el formato exacto de las secciones con los emojis."""


def _build_user_prompt(paper: Paper) -> str:
    """
    Construye el prompt del usuario con título y abstract del paper.
    
    Se incluye título y abstract como contexto para que el LLM
    genere un resumen preciso sin alucinaciones.
    """
    return f"""Título: {paper.title}

Abstract:
{paper.abstract}

Genera el resumen estructurado en español siguiendo el formato indicado."""


class LLMSummarizer:
    """
    Interfaz unificada para generar resúmenes con diferentes proveedores LLM.
    
    Patrón Strategy: el backend se selecciona en __init__ según el proveedor,
    y summarize() delega al backend correcto.
    """

    SUPPORTED_PROVIDERS = ("gemini", "openai", "ollama")

    def __init__(self, provider: str, api_key: str):
        """
        Inicializa el cliente del LLM según el proveedor.

        Args:
            provider: "gemini", "openai" o "ollama".
            api_key: API key (no requerida para Ollama).
        """
        self._provider = provider.lower().strip()
        self._api_key = api_key

        if self._provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Proveedor '{provider}' no soportado. "
                f"Opciones: {self.SUPPORTED_PROVIDERS}"
            )

        # Inicialización lazy del cliente
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """
        Inicializa el cliente del LLM.
        
        Gemini: usa google.genai.Client.
        OpenAI: usa openai.OpenAI.
        Ollama: usa ollama client (local).
        """
        if self._provider == "gemini":
            from google import genai
            self._client = genai.Client(api_key=self._api_key)

        elif self._provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
            
        elif self._provider == "ollama":
            import ollama
            self._client = ollama

    def summarize(self, paper: Paper) -> str:
        """
        Genera un resumen estructurado del paper usando el LLM configurado.

        El resumen se devuelve como texto Markdown listo para insertar
        en la nota de Obsidian, con las secciones predefinidas.
        """
        user_prompt = _build_user_prompt(paper)

        try:
            if self._provider == "gemini":
                return self._summarize_gemini(user_prompt)
            elif self._provider == "openai":
                return self._summarize_openai(user_prompt)
            elif self._provider == "ollama":
                return self._summarize_ollama(user_prompt)

        except Exception as e:
            # Capturar mensaje específico de cuota excedida para mayor claridad
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                error_msg = "Cuota de API excedida (Rate Limit). Inténtalo más tarde."
            elif "connection" in error_msg.lower() and self._provider == "ollama":
                error_msg = "No se pudo conectar con Ollama. ¿Está el servidor corriendo?"
            
            raise RuntimeError(
                f"Error al generar resumen con {self._provider}: {error_msg}"
            ) from e

    def _summarize_gemini(self, user_prompt: str) -> str:
        """Genera resumen usando Google Gemini (SDK moderno)."""
        response = self._client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.3,
            }
        )
        return response.text.strip()

    def _summarize_openai(self, user_prompt: str) -> str:
        """Genera resumen usando OpenAI Chat Completions API."""
        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()

    def _summarize_ollama(self, user_prompt: str) -> str:
        """Genera resumen usando Ollama local (Llama 3.2 3B)."""
        # Formatear el prompt con el system prompt según el formato de Ollama
        response = self._client.chat(
            model='llama3.2', # Modelo recomendado para CPU/8GB RAM
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            options={
                'temperature': 0.3,
            }
        )
        return response['message']['content'].strip()
