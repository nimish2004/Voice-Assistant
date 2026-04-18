"""
app/chat_window.py - Conversation history window for Numa.

Shows all exchanges between user and Numa in a clean chat-bubble UI.
Updates live as new commands are processed via Qt signals.

Design:
  - User messages: right-aligned, dark background
  - Numa responses: left-aligned, light background
  - Timestamps shown in muted text
  - Auto-scrolls to latest message
  - Clear history button wipes memory.json
  - Loads existing history from memory.py on open
"""

from datetime import datetime

from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QSizePolicy
)

from memory       import get_memory, clear_memory
from app.signals  import numa_signals


# ── Stylesheet ────────────────────────────────────────────────────────────────

_WINDOW_STYLE = """
    QWidget {
        background-color: #FAFAF8;
        font-family: 'Segoe UI';
    }
    QPushButton {
        background-color: transparent;
        border: 1px solid #D3D1C7;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 12px;
        color: #444441;
    }
    QPushButton:hover {
        background-color: #F1EFE8;
    }
    QPushButton:pressed {
        background-color: #D3D1C7;
    }
    QPushButton#danger {
        border-color: #E24B4A;
        color: #A32D2D;
    }
    QPushButton#danger:hover {
        background-color: #FCEBEB;
    }
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        width: 6px;
        background: transparent;
    }
    QScrollBar::handle:vertical {
        background: #D3D1C7;
        border-radius: 3px;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""


# ── Message bubble widget ─────────────────────────────────────────────────────

class MessageBubble(QFrame):
    """
    A single chat message bubble.
    role: "user" (right-aligned, dark) or "assistant" (left-aligned, light)
    """

    def __init__(self, role: str, text: str, timestamp: str = "", parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 2, 0, 2)

        is_user = (role == "user")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 4, 16, 4)
        outer.setSpacing(0)

        # Spacer pushes bubble to correct side
        if is_user:
            outer.addStretch()

        # Bubble container
        bubble = QFrame()
        bubble.setMaximumWidth(420)
        bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Minimum,
        )

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 10, 14, 10)
        bubble_layout.setSpacing(4)

        # Message text
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Segoe UI", 11))

        if is_user:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #2C2C2A;
                    border-radius: 16px;
                    border-bottom-right-radius: 4px;
                }
            """)
            msg_label.setStyleSheet("color: #FFFFFF;")
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #F1EFE8;
                    border-radius: 16px;
                    border-bottom-left-radius: 4px;
                    border: 0.5px solid #D3D1C7;
                }
            """)
            msg_label.setStyleSheet("color: #2C2C2A;")

        bubble_layout.addWidget(msg_label)

        # Timestamp
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setFont(QFont("Segoe UI", 9))
            time_label.setStyleSheet("color: #888780; background: transparent;")
            if is_user:
                time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            bubble_layout.addWidget(time_label)

        outer.addWidget(bubble)

        if not is_user:
            outer.addStretch()


# ── Chat window ───────────────────────────────────────────────────────────────

class ChatWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Numa — Conversation")
        self.setMinimumSize(480, 600)
        self.resize(520, 680)
        self.setStyleSheet(_WINDOW_STYLE)

        self._build_ui()
        self._load_history()

        # Connect live update signals
        numa_signals.command_received.connect(self._on_command)
        numa_signals.response_spoken.connect(self._on_response)
        numa_signals.status_changed.connect(self._on_status)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #D3D1C7;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 16, 0)

        title = QLabel("Conversation")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        title.setStyleSheet("color: #2C2C2A;")

        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont("Segoe UI", 10))
        self._status_dot.setStyleSheet("color: #1D9E75;")

        self._status_label = QLabel("Ready")
        self._status_label.setFont(QFont("Segoe UI", 11))
        self._status_label.setStyleSheet("color: #888780;")

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("danger")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self._clear_history)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self._status_dot)
        header_layout.addSpacing(4)
        header_layout.addWidget(self._status_label)
        header_layout.addSpacing(12)
        header_layout.addWidget(clear_btn)

        root.addWidget(header)

        # ── Scroll area for messages ───────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._messages_container = QWidget()
        self._messages_container.setStyleSheet(
            "background-color: #FAFAF8;"
        )
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setContentsMargins(0, 16, 0, 16)
        self._messages_layout.setSpacing(4)
        self._messages_layout.addStretch()   # pushes messages to bottom

        self._scroll.setWidget(self._messages_container)
        root.addWidget(self._scroll)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-top: 1px solid #D3D1C7;
            }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)

        self._count_label = QLabel("No exchanges yet")
        self._count_label.setFont(QFont("Segoe UI", 10))
        self._count_label.setStyleSheet("color: #888780;")

        footer_layout.addWidget(self._count_label)
        footer_layout.addStretch()

        root.addWidget(footer)

    # ── History loading ───────────────────────────────────────────────────────

    def _load_history(self):
        """Load existing memory.json and populate bubbles."""
        history = get_memory()
        if not history:
            self._add_empty_state()
            return

        # Group into exchanges: user + assistant pairs
        for msg in history:
            role      = msg.get("role", "user")
            content   = msg.get("content", "")
            timestamp = msg.get("timestamp", "")

            # Format timestamp for display
            display_time = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    display_time = dt.strftime("%I:%M %p")
                except Exception:
                    pass

            self._add_bubble(role, content, display_time)

        self._update_count()
        self._scroll_to_bottom()

    def _add_empty_state(self):
        """Show placeholder when no history exists."""
        label = QLabel("No conversation history yet.\nSay the wake word to start.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Segoe UI", 12))
        label.setStyleSheet("color: #B4B2A9; padding: 40px;")
        label.setObjectName("empty_state")
        # Insert before the stretch
        self._messages_layout.insertWidget(0, label)

    def _remove_empty_state(self):
        """Remove placeholder once real messages arrive."""
        for i in range(self._messages_layout.count()):
            item = self._messages_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if w.objectName() == "empty_state":
                    w.deleteLater()
                    break

    # ── Message management ────────────────────────────────────────────────────

    def _add_bubble(self, role: str, text: str, timestamp: str = ""):
        """Add a message bubble. Inserts before the trailing stretch."""
        # Skip task labels stored in memory like [task: open_spotify]
        if text.startswith("[task:"):
            return

        bubble = MessageBubble(role, text, timestamp)
        # Insert before the stretch item (last item)
        insert_pos = self._messages_layout.count() - 1
        self._messages_layout.insertWidget(insert_pos, bubble)

    def _scroll_to_bottom(self):
        """Scroll to the latest message."""
        QTimer.singleShot(
            50,
            lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            )
        )

    def _update_count(self):
        """Update footer exchange counter."""
        history = get_memory()
        # Count only user turns (each user turn = one exchange)
        count = sum(1 for m in history if m.get("role") == "user")
        if count == 0:
            self._count_label.setText("No exchanges yet")
        elif count == 1:
            self._count_label.setText("1 exchange")
        else:
            self._count_label.setText(f"{count} exchanges")

    def _clear_history(self):
        """Clear all messages from UI and memory."""
        clear_memory()

        # Remove all bubbles
        while self._messages_layout.count() > 1:   # keep the stretch
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._add_empty_state()
        self._count_label.setText("No exchanges yet")

    # ── Signal handlers (called from main thread via Qt) ─────────────────────

    def _on_command(self, user_text: str, intent: str):
        """New user command received — add user bubble."""
        self._remove_empty_state()
        now = datetime.now().strftime("%I:%M %p")
        self._add_bubble("user", user_text, now)
        self._update_count()
        self._scroll_to_bottom()

    def _on_response(self, response_text: str):
        """Numa spoke a response — add assistant bubble."""
        self._remove_empty_state()
        now = datetime.now().strftime("%I:%M %p")
        self._add_bubble("assistant", response_text, now)
        self._scroll_to_bottom()

    def _on_status(self, status: str):
        """Update status indicator in header."""
        color_map = {
            "idle"       : "#1D9E75",
            "listening"  : "#1D9E75",
            "processing" : "#BA7517",
            "speaking"   : "#185FA5",
            "muted"      : "#A32D2D",
            "error"      : "#888780",
        }
        label_map = {
            "idle"       : "Ready",
            "listening"  : "Listening...",
            "processing" : "Thinking...",
            "speaking"   : "Speaking...",
            "muted"      : "Muted",
            "error"      : "Error",
        }
        color = color_map.get(status, "#1D9E75")
        self._status_dot.setStyleSheet(f"color: {color};")
        self._status_label.setText(label_map.get(status, ""))

    def closeEvent(self, event):
        """Hide instead of destroy so window state is preserved."""
        event.ignore()
        self.hide()
