#!/bin/bash
# Script de lanzamiento para Paper Scout
# Navega a la carpeta del proyecto, activa el venv y lanza la App.

# Detectar directorio del script (funciona desde cualquier ubicación)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

cd "$PROJECT_DIR" || exit

# Activar venv si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Lanzar aplicación
python main.py
