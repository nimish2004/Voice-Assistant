"""
app/signals.py - Central Qt signal bus for Numa.

WHY THIS EXISTS:
  The wake engine runs in a daemon thread.
  The UI (tray, chat window) runs on the main thread.
  Qt signals are the ONLY safe way to communicate between threads in PyQt6.
  Calling UI methods directly from a background thread = crash.

HOW IT WORKS:
  1. Wake engine thread emits a signal (e.g. command_received)
  2. Qt queues it automatically
  3. Main thread delivers it to all connected slots
  No locks, no shared state, no race conditions.

HOW TO USE:
  From any module:
    from app.signals import numa_signals

  To emit (from wake thread):
    numa_signals.command_received.emit("open spotify", "open_spotify")

  To connect (from UI):
    numa_signals.command_received.connect(self.on_command)
"""

from PyQt6.QtCore import QObject, pyqtSignal


class NumaSignals(QObject):
    """
    Single instance signal bus. Import numa_signals everywhere.
    Never instantiate this class directly outside this module.
    """

    # Emitted when user speaks a command
    # args: (user_text: str, intent: str)
    command_received = pyqtSignal(str, str)

    # Emitted when Numa speaks a response
    # args: (response_text: str)
    response_spoken = pyqtSignal(str)

    # Emitted when wake word is detected (before transcription)
    wake_detected = pyqtSignal()

    # Emitted when Numa starts listening for a command
    listening_started = pyqtSignal()

    # Emitted when transcription is complete
    # args: (text: str)
    transcription_done = pyqtSignal(str)

    # Emitted when assistant state changes
    # args: (status: str) — "listening", "processing", "speaking", "idle"
    status_changed = pyqtSignal(str)

    # Emitted when settings are saved from the settings window
    settings_saved = pyqtSignal()

    # Emitted when Numa is asked to quit via voice or menu
    quit_requested = pyqtSignal()


# Module-level singleton — import this everywhere
numa_signals = NumaSignals()
