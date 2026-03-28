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


# ──────────────────────────────────────────────────
# System prompt para generación de palabras clave
# ──────────────────────────────────────────────────
KEYWORDS_SYSTEM_PROMPT = """Eres un experto en búsqueda bibliográfica académica.
Tu tarea es convertir una descripción de un tema de investigación en una lista de 3 a 5 términos de búsqueda (keywords o frases) optimizados para la API de arXiv.

REGLAS:
- Devuelve ÚNICAMENTE los términos separados por comas.
- No incluyas explicaciones, introducciones ni numeración.
- Los términos deben ser técnicos y específicos.
- Ejemplo de salida: transformer, long context, audio processing, sparse attention
"""


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

    SUPPORTED_PROVIDERS = ("gemini", "openai", "ollama", "claude")

    def __init__(self, provider: str, api_key: str, use_gpu: bool = False):
        """
        Inicializa el cliente del LLM según el proveedor.

        Args:
            provider: "gemini", "openai", "claude" o "ollama".
            api_key: API key (no requerida para Ollama).
            use_gpu: Si True, intenta aceleración por GPU (Ollama).
        """
        self._provider = provider.lower().strip()
        self._api_key = api_key
        self._use_gpu = use_gpu

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
        """
        if self._provider == "gemini":
            from google import genai
            self._client = genai.Client(api_key=self._api_key)

        elif self._provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
            
        elif self._provider == "claude":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
            
        elif self._provider == "ollama":
            import ollama
            self._client = ollama

    def summarize(self, paper: Paper) -> str:
        """Genera un resumen estructurado del paper."""
        user_prompt = _build_user_prompt(paper)
        return self._generate(SYSTEM_PROMPT, user_prompt)

    def generate_keywords(self, description: str) -> str:
        """
        Genera palabras clave optimizadas a partir de una descripción.
        """
        user_prompt = f"Descripción del tema: {description}\n\nGenera los términos de búsqueda:"
        return self._generate(KEYWORDS_SYSTEM_PROMPT, user_prompt)

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """Método genérico para llamar al LLM con prompts específicos."""
        try:
            if self._provider == "gemini":
                return self._call_gemini(system_prompt, user_prompt)
            elif self._provider == "openai":
                return self._call_openai(system_prompt, user_prompt)
            elif self._provider == "claude":
                return self._call_claude(system_prompt, user_prompt)
            elif self._provider == "ollama":
                return self._call_ollama(system_prompt, user_prompt)

        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                error_msg = "Cuota de API excedida. Inténtalo más tarde."
            elif "connection" in error_msg.lower() and self._provider == "ollama":
                error_msg = "Error de conexión con Ollama local."
            
            raise RuntimeError(f"Error con {self._provider}: {error_msg}") from e

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Llamada directa a Gemini."""
        response = self._client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.3,
            }
        )
        return response.text.strip()

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Llamada directa a OpenAI."""
        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Llamada directa a Ollama."""
        # Configuración de aceleración
        options = {'temperature': 0.3}
        if self._use_gpu:
            # Forzar offloading de capas (35 es suficiente para Llama 3.2 3B)
            options['num_gpu'] = 35

        response = self._client.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            options=options
        )
        return response['message']['content'].strip()

    def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Llamada directa a Anthropic Claude."""
        response = self._client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        # Claude devuelve una lista de bloques de contenido
        return response.content[0].text.strip()
