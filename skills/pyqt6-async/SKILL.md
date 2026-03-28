---
name: PyQt6 Async Threading
description: Reglas estrictas sobre cómo conectar el pipeline de backend con la UI de PyQt6 usando hilos asíncronos (QThread + Worker Object Pattern).
---

# PyQt6 Async Threading — Reglas Obligatorias

## 1. Patrón Worker Object (OBLIGATORIO)

**NUNCA subclasear `QThread` directamente.** Siempre usar el patrón Worker Object:

```python
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

class MyWorker(QObject):
    """El worker HEREDA de QObject, NO de QThread."""
    
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)  # (current, total)
    log = pyqtSignal(str, str)       # (message, level)
    
    @pyqtSlot()
    def run(self):
        """Toda la lógica de negocio va aquí."""
        ...
        self.finished.emit()
```

## 2. Ciclo de Vida del Thread

```python
# En el controlador o ventana principal:
self.thread = QThread()
self.worker = MyWorker(params)
self.worker.moveToThread(self.thread)

# Conexiones OBLIGATORIAS:
self.thread.started.connect(self.worker.run)
self.worker.finished.connect(self.thread.quit)
self.worker.finished.connect(self.worker.deleteLater)
self.thread.finished.connect(self.thread.deleteLater)

# Conexiones de UI:
self.worker.progress.connect(self.update_progress_bar)
self.worker.log.connect(self.append_log)

self.thread.start()
```

## 3. Reglas de Seguridad de Hilos

### ❌ PROHIBIDO
- Acceder a widgets de Qt desde un hilo que no sea el principal
- Modificar `QTextEdit`, `QLabel`, `QProgressBar`, etc. directamente desde el worker
- Usar `time.sleep()` en el hilo principal
- Compartir estado mutable sin sincronización

### ✅ OBLIGATORIO
- Usar `pyqtSignal` para TODO dato que vaya del worker → UI
- Decorar slots con `@pyqtSlot()` para rendimiento
- Usar `threading.Event()` para flags de cancelación
- Almacenar referencias al thread y worker (`self.thread`, `self.worker`) para evitar garbage collection prematura

## 4. Cancelación Segura

```python
import threading

class MyWorker(QObject):
    def __init__(self):
        super().__init__()
        self._cancel_event = threading.Event()
    
    def cancel(self):
        """Llamado desde el hilo principal."""
        self._cancel_event.set()
    
    @pyqtSlot()
    def run(self):
        for i, item in enumerate(items):
            if self._cancel_event.is_set():
                self.log.emit("Pipeline cancelado por el usuario", "warn")
                break
            # ... procesar item ...
        self.finished.emit()
```

## 5. Manejo de Errores

```python
@pyqtSlot()
def run(self):
    try:
        # ... lógica del pipeline ...
        self.finished.emit(True, "Completado exitosamente")
    except Exception as e:
        self.log.emit(f"Error: {str(e)}", "error")
        self.finished.emit(False, str(e))
```

## 6. Checklist Pre-Commit

Antes de hacer commit de cualquier código que involucre threading:

- [ ] ¿El worker hereda de `QObject`, no de `QThread`?
- [ ] ¿Se usa `moveToThread()` para asignar el worker al thread?
- [ ] ¿Se conectan `finished → quit`, `finished → deleteLater`?
- [ ] ¿Se guardan referencias al thread y worker para evitar GC?
- [ ] ¿Toda comunicación worker→UI es vía señales?
- [ ] ¿Se implementa cancelación con `threading.Event`?
- [ ] ¿Se manejan excepciones dentro del `run()`?
