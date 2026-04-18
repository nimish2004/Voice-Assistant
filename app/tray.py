"""
app/tray.py - System tray icon and application shell for Numa.
"""

import threading

from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QAction
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu
)

import state
from config.settings import settings
from app.signals     import numa_signals


# ── Icon generator ────────────────────────────────────────────────────────────

def _make_icon(color: str, status: str = "idle") -> QIcon:
    """Programmatic tray icon — colored circle with N, dot indicator."""
    px = QPixmap(64, 64)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Main circle
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 56, 56)

    # Letter N
    p.setPen(QColor("white"))
    f = QFont("Segoe UI", 24, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "N")

    # Status dot (bottom-right)
    dot_colors = {
        "listening"  : "#1D9E75",
        "processing" : "#EF9F27",
        "speaking"   : "#378ADD",
        "muted"      : "#E24B4A",
        "error"      : "#888780",
        "idle"       : None,   # no dot when idle
    }
    dot_color = dot_colors.get(status)
    if dot_color:
        p.setBrush(QColor(dot_color))
        p.setPen(QPen(QColor("white"), 2))
        p.drawEllipse(42, 42, 18, 18)

    p.end()
    return QIcon(px)


_STATUS_COLORS = {
    "idle"       : "#2C2C2A",
    "listening"  : "#2C2C2A",
    "processing" : "#2C2C2A",
    "speaking"   : "#2C2C2A",
    "muted"      : "#A32D2D",
    "error"      : "#888780",
}

_STATUS_LABELS = {
    "idle"       : "Ready",
    "listening"  : "Listening...",
    "processing" : "Thinking...",
    "speaking"   : "Speaking...",
    "muted"      : "Muted",
    "error"      : "Error",
}


# ── Tray app ──────────────────────────────────────────────────────────────────

class NumaTray:

    def __init__(self, app: QApplication):
        self._app              = app
        self._status           = "idle"
        self._chat_window      = None
        self._settings_window  = None

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(_make_icon(_STATUS_COLORS["idle"], "idle"))
        self._tray.setToolTip("Numa — Ready")
        self._tray.activated.connect(self._on_activated)
        self._tray.setContextMenu(self._build_menu())
        self._tray.show()

        numa_signals.status_changed.connect(self._on_status)
        numa_signals.quit_requested.connect(self._quit)
        numa_signals.settings_saved.connect(self._on_settings_saved)

        QTimer.singleShot(800, self._startup_toast)

    def _build_menu(self) -> QMenu:
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: #FFFFFF;
                border: 1px solid #D3D1C7;
                border-radius: 10px;
                padding: 6px;
                font-family: 'Segoe UI';
                font-size: 13px;
                color: #2C2C2A;
            }
            QMenu::item {
                padding: 9px 20px 9px 14px;
                border-radius: 6px;
                min-width: 180px;
            }
            QMenu::item:selected { background: #F1EFE8; }
            QMenu::item:disabled { color: #B4B2A9; }
            QMenu::separator {
                height: 1px;
                background: #E8E6E0;
                margin: 4px 10px;
            }
        """)

        self._header_action = menu.addAction("Numa  •  Ready")
        self._header_action.setEnabled(False)
        menu.addSeparator()

        chat_act = menu.addAction("Chat History")
        chat_act.triggered.connect(self._open_chat)

        settings_act = menu.addAction("Settings")
        settings_act.triggered.connect(self._open_settings)

        menu.addSeparator()

        self._mute_act = menu.addAction("Mute Numa")
        self._mute_act.setCheckable(True)
        self._mute_act.triggered.connect(self._toggle_mute)

        recal_act = menu.addAction("Recalibrate Mic")
        recal_act.triggered.connect(self._recalibrate)

        setup_act = menu.addAction("Run Setup Again")
        setup_act.triggered.connect(self._run_setup)

        menu.addSeparator()

        quit_act = menu.addAction("Quit Numa")
        quit_act.triggered.connect(self._quit)

        return menu

    def _on_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self._open_chat()

    def _on_status(self, status: str):
        self._status = status
        color = _STATUS_COLORS.get(status, "#2C2C2A")
        self._tray.setIcon(_make_icon(color, status))
        label = f"Numa  •  {_STATUS_LABELS.get(status, 'Ready')}"
        self._header_action.setText(label)
        self._tray.setToolTip(label)

    def _open_chat(self):
        if self._chat_window is None:
            from app.chat_window import ChatWindow
            self._chat_window = ChatWindow()
        self._chat_window.show()
        self._chat_window.raise_()
        self._chat_window.activateWindow()

    def _open_settings(self):
        if self._settings_window is None:
            from app.settings_window import SettingsWindow
            self._settings_window = SettingsWindow()
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

    def _toggle_mute(self, checked: bool):
        new_state = state.toggle_mute()
        status    = "muted" if new_state else "idle"
        self._on_status(status)
        self._mute_act.setText("Unmute Numa" if new_state else "Mute Numa")
        msg = ("Muted", "Voice output off. Commands still work.") if new_state \
              else ("Unmuted", "Voice output back on.")
        self._tray.showMessage(msg[0], msg[1],
            QSystemTrayIcon.MessageIcon.Information, 2000)

    def _recalibrate(self):
        self._on_status("processing")
        self._tray.showMessage("Calibrating Mic",
            "Stay silent for 2 seconds...",
            QSystemTrayIcon.MessageIcon.Information, 3000)

        def _do():
            from speech import recalibrate
            recalibrate()
            numa_signals.status_changed.emit("idle")
            self._tray.showMessage("Done",
                "Microphone calibrated.",
                QSystemTrayIcon.MessageIcon.Information, 2000)

        threading.Thread(target=_do, daemon=True).start()

    def _on_settings_saved(self):
        self._tray.showMessage("Settings Saved",
            "Changes applied.",
            QSystemTrayIcon.MessageIcon.Information, 2000)

    def _startup_toast(self):
        wake = settings.get("wake_word", "alexa").title()
        self._tray.showMessage(
            "Numa is running",
            f"Say '{wake}' to wake me up. Right-click the tray icon for options.",
            QSystemTrayIcon.MessageIcon.Information, 3500)

    def _run_setup(self):
        """Force onboarding to show on next launch, then restart."""
        from app.onboarding import force_onboarding
        force_onboarding()
        state.stop()
        import sys, subprocess
        subprocess.Popen([sys.executable, "main.py"])
        self._app.quit()

    def _quit(self):
        state.stop()
        self._app.quit()