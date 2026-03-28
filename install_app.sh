#!/bin/bash
# Script de instalación para Paper Scout en Linux (Desktop Integration)

PROJECT_DIR="/home/marco/paper-scout"
APPS_DIR="$HOME/.local/share/applications"

echo "🚀 Iniciando integración de Paper Scout..."

# 1. Dar permisos de ejecución
chmod +x "$PROJECT_DIR/launcher.sh"
chmod +x "$PROJECT_DIR/install_app.sh"

# 2. Registrar el archivo .desktop
if [ ! -d "$APPS_DIR" ]; then
    mkdir -p "$APPS_DIR"
fi

cp "$PROJECT_DIR/paper-scout.desktop" "$APPS_DIR/"

# 3. Notificar al sistema
if hash update-desktop-database 2>/dev/null; then
    update-desktop-database "$APPS_DIR"
fi

echo "✅ Instalación completada con éxito."
echo "💡 Ya puedes buscar 'Paper Scout' en tu menú de aplicaciones."
