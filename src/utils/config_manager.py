"""
config_manager.py — Persistencia de configuración entre sesiones.

Guarda y carga la configuración del usuario en:
  ~/.config/paper-scout/config.json

Campos persistidos:
  - vault_path: Ruta del vault de Obsidian
  - provider: Proveedor LLM seleccionado (gemini/openai)
  - max_results: Número máximo de resultados
  - keywords: Últimas palabras clave usadas

La API key NUNCA se persiste por seguridad.
"""

import json
from pathlib import Path
from typing import Any, Optional


# Ruta estándar XDG para configuración en Linux
CONFIG_DIR = Path.home() / ".config" / "paper-scout"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Valores por defecto
DEFAULT_CONFIG: dict[str, Any] = {
    "vault_path": "",
    "provider": "openai",
    "max_results": 10,
    "keywords": "",
}


def load_config() -> dict[str, Any]:
    """
    Carga la configuración desde disco.
    
    Si el archivo no existe o está corrupto, retorna los valores por defecto.
    Nunca lanza excepciones.
    
    Returns:
        Diccionario con la configuración del usuario.
    """
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            # Merge con defaults para manejar campos nuevos
            config = {**DEFAULT_CONFIG, **data}
            return config
    except (json.JSONDecodeError, OSError):
        pass

    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> bool:
    """
    Guarda la configuración en disco.
    
    Crea el directorio ~/.config/paper-scout/ si no existe.
    Nunca persiste la API key.
    
    Args:
        config: Diccionario con la configuración a guardar.
    
    Returns:
        True si se guardó exitosamente, False si hubo error.
    """
    try:
        # Filtrar la API key si existe (NUNCA persistir)
        safe_config = {k: v for k, v in config.items() if k != "api_key"}
        
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(safe_config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True

    except OSError:
        return False
