"""
notifier.py — Notificaciones de escritorio para Linux.

Usa subprocess para lanzar `notify-send` (libnotify).
Si notify-send no está instalado, logea un warning sin crashear.
"""

import subprocess
import shutil
from typing import Optional


def notify(
    title: str,
    message: str,
    icon: str = "dialog-information",
    urgency: str = "normal",
    timeout_ms: int = 5000,
) -> bool:
    """
    Envía una notificación de escritorio en Linux usando notify-send.
    
    Args:
        title: Título de la notificación.
        message: Cuerpo de la notificación.
        icon: Nombre del icono (del tema de iconos del sistema).
              Valores comunes: dialog-information, dialog-warning, dialog-error.
        urgency: Nivel de urgencia: low, normal, critical.
        timeout_ms: Tiempo de visualización en milisegundos.

    Returns:
        True si la notificación se envió exitosamente, False si no.
    """
    # Verificar que notify-send existe en el PATH
    if not shutil.which("notify-send"):
        return False

    try:
        subprocess.run(
            [
                "notify-send",
                "-i", icon,
                "-u", urgency,
                "-t", str(timeout_ms),
                title,
                message,
            ],
            timeout=5,   # Timeout del proceso para evitar bloqueos
            check=False,  # No lanzar excepción en exit code != 0
            capture_output=True,
        )
        return True

    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        return False
