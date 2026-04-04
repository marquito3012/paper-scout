#!/bin/bash
# Script de desinstalación para Paper Scout - Multi-distro Linux

set -e

# =============================================================================
# 1. Detectar directorio del proyecto
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# =============================================================================
# 2. Detectar distribución de Linux
# =============================================================================
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            ubuntu|debian|linuxmint|pop)
                OS_FAMILY="debian"
                OS_NAME="$PRETTY_NAME"
                ;;
            arch|manjaro|endeavouros|artix|cachyos)
                OS_FAMILY="arch"
                OS_NAME="$PRETTY_NAME"
                ;;
            fedora|rhel|centos|rocky|almalinux)
                OS_FAMILY="fedora"
                OS_NAME="$PRETTY_NAME"
                ;;
            *)
                OS_FAMILY="unknown"
                OS_NAME="$PRETTY_NAME"
                ;;
        esac
    elif [ -f /etc/arch-release ]; then
        OS_FAMILY="arch"
        OS_NAME="Arch Linux"
    else
        OS_FAMILY="unknown"
        OS_NAME="Unknown Linux"
    fi
}

detect_os

APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
DESKTOP_FILE="paper-scout.desktop"
ICON_FILE="paper-scout.png"

echo "🗑️  Iniciando desinstalación de Paper Scout..."
echo "📁 Directorio del proyecto: $PROJECT_DIR"
echo "🐧 Sistema: $OS_NAME"
echo ""

# 1. Eliminar el archivo .desktop
if [ -f "$APPS_DIR/$DESKTOP_FILE" ]; then
    rm "$APPS_DIR/$DESKTOP_FILE"
    echo "✅ Acceso directo eliminado de $APPS_DIR"
else
    echo "ℹ️  No se encontró el acceso directo en $APPS_DIR"
fi

# 2. Eliminar el icono del sistema
if [ -f "$ICONS_DIR/$ICON_FILE" ]; then
    rm "$ICONS_DIR/$ICON_FILE"
    echo "✅ Icono eliminado de $ICONS_DIR"
else
    echo "ℹ️  No se encontró el icono en $ICONS_DIR"
fi

# 3. Notificar al sistema
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
    echo "✅ Base de datos de escritorio actualizada"
fi

# 4. Actualizar caché de iconos
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo ""
echo "✅ Desintegración del sistema completada."
echo ""
echo "💡 Nota: Los archivos del proyecto y el entorno virtual en '$PROJECT_DIR' NO han sido eliminados."
echo "💡 Si deseas borrar TODO, puedes ejecutar: rm -rf '$PROJECT_DIR'"
echo ""
