#!/bin/bash
# Script de desinstalación para Paper Scout en Linux (Desktop Integration)

APPS_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="paper-scout.desktop"

echo "🗑️ Iniciando desinstalación de Paper Scout..."

# 1. Eliminar el archivo .desktop
if [ -f "$APPS_DIR/$DESKTOP_FILE" ]; then
    rm "$APPS_DIR/$DESKTOP_FILE"
    echo "✅ Acceso directo eliminado."
else
    echo "ℹ️ No se encontró el acceso directo en el sistema."
fi

# 2. Notificar al sistema
if hash update-desktop-database 2>/dev/null; then
    update-desktop-database "$APPS_DIR"
fi

# 3. Informar sobre el resto de archivos
echo "✅ Desintegración del sistema completada."
echo "💡 Nota: Los archivos del proyecto y el entorno virtual en '$(pwd)' NO han sido eliminados."
echo "💡 Si deseas borrar TODO, puedes ejecutar: rm -rf '$(pwd)'"
