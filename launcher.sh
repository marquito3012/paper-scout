#!/bin/bash
# Script de lanzamiento para Paper Scout
# Navega a la carpeta del proyecto, activa el venv y lanza la App.

PROJECT_DIR="/home/marco/paper-scout"
cd "$PROJECT_DIR" || exit

# Activar venv si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Lanzar aplicación
python main.py
