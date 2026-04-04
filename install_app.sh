#!/bin/bash
# Script de instalación para Paper Scout - Multi-distro Linux

set -e

# =============================================================================
# 1. Detectar directorio del proyecto (funciona desde cualquier ubicación)
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "📁 Directorio del proyecto: $PROJECT_DIR"

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
            opensuse*|suse)
                OS_FAMILY="suse"
                OS_NAME="$PRETTY_NAME"
                ;;
            *)
                OS_FAMILY="unknown"
                OS_NAME="$PRETTY_NAME"
                ;;
        esac
        echo "🐧 Sistema detectado: $OS_NAME (Familia: $OS_FAMILY)"
    elif [ -f /etc/arch-release ]; then
        OS_FAMILY="arch"
        OS_NAME="Arch Linux"
        echo "🐧 Sistema detectado: $OS_NAME"
    else
        OS_FAMILY="unknown"
        OS_NAME="Unknown Linux"
        echo "⚠️  Sistema no detectado, usando configuración genérica..."
    fi
}

detect_os

# =============================================================================
# 3. Verificar dependencias según OS
# =============================================================================
check_dependencies() {
    echo "🔍 Verificando dependencias..."

    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: Python 3 no está instalado."
        case "$OS_FAMILY" in
            debian)
                echo "   Instala: sudo apt install python3 python3-pip python3-venv"
                ;;
            arch)
                echo "   Instala: sudo pacman -S python python-pip"
                ;;
            fedora)
                echo "   Instala: sudo dnf install python3 python3-pip"
                ;;
            *)
                echo "   Instala Python 3.10+ desde tu gestor de paquetes"
                ;;
        esac
        exit 1
    fi

    # Verificar desktop-file-utils (para update-desktop-database)
    if ! command -v update-desktop-database &> /dev/null; then
        echo "⚠️  update-desktop-database no encontrado."
        case "$OS_FAMILY" in
            debian)
                echo "   Instala: sudo apt install desktop-file-utils"
                ;;
            arch)
                echo "   Instala: sudo pacman -S desktop-file-utils"
                ;;
            fedora)
                echo "   Instala: sudo dnf install desktop-file-utils"
                ;;
        esac
        SKIP_UPDATE_DB=true
    else
        SKIP_UPDATE_DB=false
    fi
}

check_dependencies

# =============================================================================
# 4. Crear entorno virtual e instalar dependencias
# =============================================================================
setup_python_env() {
    echo ""
    echo "🐍 Configurando entorno de Python..."

    VENV_DIR="$PROJECT_DIR/.venv"

    # Crear entorno virtual si no existe
    if [ ! -d "$VENV_DIR" ]; then
        echo "   Creando entorno virtual en .venv..."
        python3 -m venv "$VENV_DIR"
    else
        echo "   Entorno virtual existente encontrado."
    fi

    # Activar entorno
    source "$VENV_DIR/bin/activate"

    # Actualizar pip
    echo "   Actualizando pip..."
    pip install --upgrade pip --quiet

    # Instalar dependencias
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        echo "   Instalando dependencias de requirements.txt..."
        pip install -r "$PROJECT_DIR/requirements.txt"
        echo "✅ Dependencias de Python instaladas."
    else
        echo "⚠️  No se encontró requirements.txt"
    fi

    deactivate
}

setup_python_env

# =============================================================================
# 5. Instalar integración de escritorio
# =============================================================================
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "🚀 Iniciando integración de Paper Scout..."

# Crear directorios necesarios
mkdir -p "$APPS_DIR"
mkdir -p "$ICONS_DIR"

# Dar permisos de ejecución
chmod +x "$PROJECT_DIR/launcher.sh"
chmod +x "$PROJECT_DIR/install_app.sh"
chmod +x "$PROJECT_DIR/uninstall_app.sh"

# Copiar archivo .desktop reemplazando el placeholder con la ruta real
sed "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" "$PROJECT_DIR/paper-scout.desktop" > "$APPS_DIR/paper-scout.desktop"
echo "✅ Archivo .desktop instalado en $APPS_DIR"

# Copiar icono al directorio de iconos del sistema
if [ -f "$PROJECT_DIR/assets/app_icon.png" ]; then
    cp "$PROJECT_DIR/assets/app_icon.png" "$ICONS_DIR/paper-scout.png"
    echo "✅ Icono instalado en $ICONS_DIR"
fi

# Actualizar base de datos de escritorio
if [ "$SKIP_UPDATE_DB" = false ]; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
    echo "✅ Base de datos de escritorio actualizada"
fi

# Actualizar caché de iconos (si está disponible)
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo ""
echo "✅ Instalación completada con éxito."
echo "💡 Ya puedes buscar 'Paper Scout' en tu menú de aplicaciones."
echo ""
echo "📝 Notas para $OS_NAME:"
case "$OS_FAMILY" in
    arch)
        echo "   - En Arch/Manjaro, puede tomar unos segundos en aparecer en el menú."
        echo "   - Si usas GNOME, ejecuta: gtk-update-icon-cache -f $HOME/.local/share/icons/hicolor"
        ;;
    debian)
        echo "   - En Ubuntu/Debian, la app debería aparecer inmediatamente."
        ;;
    fedora)
        echo "   - En Fedora, si no aparece, cierra sesión y vuelve a entrar."
        ;;
esac
