"""
app/settings_window.py - Settings UI for Numa.

Exposes every key in config/settings.py as a form control.
On save, validates via settings.set() (which type-checks and range-checks).
Invalid values show an inline error — never silently ignored.

Controls used per type:
  str with known options -> QComboBox (dropdown)
  str freeform           -> QLineEdit
  int / float            -> QSpinBox / QDoubleSpinBox or QSlider
  bool                   -> QCheckBox (toggle)
"""

from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QLineEdit, QComboBox, QSlider, QCheckBox,
    QPushButton, QFrame, QMessageBox, QSpinBox, QDoubleSpinBox,
    QSizePolicy
)

from config.settings import settings
from app.signals     import numa_signals


# ── Stylesheet ────────────────────────────────────────────────────────────────

_STYLE = """
    QWidget {
        background-color: #FAFAF8;
        font-family: 'Segoe UI';
        font-size: 13px;
        color: #2C2C2A;
    }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background-color: #FFFFFF;
        border: 1px solid #D3D1C7;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
        color: #2C2C2A;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #888780;
    }
    QComboBox::drop-down {
        border: none;
        padding-right: 8px;
    }
    QSlider::groove:horizontal {
        height: 4px;
        background: #D3D1C7;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        width: 18px;
        height: 18px;
        background: #2C2C2A;
        border-radius: 9px;
        margin: -7px 0;
    }
    QSlider::sub-page:horizontal {
        background: #2C2C2A;
        border-radius: 2px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 1px solid #D3D1C7;
        border-radius: 4px;
        background: white;
    }
    QCheckBox::indicator:checked {
        background: #2C2C2A;
        border-color: #2C2C2A;
    }
    QPushButton#save {
        background-color: #2C2C2A;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 32px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton#save:hover {
        background-color: #444441;
    }
    QPushButton#reset {
        background-color: transparent;
        border: 1px solid #D3D1C7;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 13px;
        color: #888780;
    }
    QPushButton#reset:hover {
        background-color: #F1EFE8;
    }
    QScrollArea { border: none; }
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


# ── Section header ────────────────────────────────────────────────────────────

class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.setStyleSheet("color: #888780; letter-spacing: 1px; padding-top: 8px;")


# ── Setting row ───────────────────────────────────────────────────────────────

class SettingRow(QFrame):
    """
    One row: label on the left, control on the right.
    Optional description text below the label.
    """
    def __init__(self, label: str, control: QWidget,
                 description: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: transparent; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(16)

        # Left: label + optional description
        left = QVBoxLayout()
        left.setSpacing(2)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 12))
        lbl.setStyleSheet("color: #2C2C2A;")
        left.addWidget(lbl)

        if description:
            desc = QLabel(description)
            desc.setFont(QFont("Segoe UI", 10))
            desc.setStyleSheet("color: #888780;")
            left.addWidget(desc)

        layout.addLayout(left, stretch=2)

        # Right: control
        control.setFixedWidth(200)
        layout.addWidget(control, stretch=1, alignment=Qt.AlignmentFlag.AlignRight)


# ── Settings window ───────────────────────────────────────────────────────────

class SettingsWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Numa — Settings")
        self.setMinimumSize(520, 640)
        self.resize(560, 720)
        self.setStyleSheet(_STYLE)

        # Track all controls: key -> widget
        self._controls: dict[str, QWidget] = {}

        self._build_ui()
        self._load_values()

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
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        title.setStyleSheet("color: #2C2C2A;")
        h_layout.addWidget(title)
        root.addWidget(header)

        # ── Scrollable form body ──────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body.setStyleSheet("background-color: #FAFAF8;")
        form = QVBoxLayout(body)
        form.setContentsMargins(24, 16, 24, 24)
        form.setSpacing(4)

        # ── Wake Word section ─────────────────────────────────────────────────
        form.addWidget(SectionHeader("Wake Word"))
        form.addWidget(self._divider())

        wake_input = QLineEdit()
        wake_input.setPlaceholderText("e.g. alexa")
        self._controls["wake_word"] = wake_input
        form.addWidget(SettingRow(
            "Wake word",
            wake_input,
            "The word that activates Numa"
        ))

        threshold_slider = QSlider(Qt.Orientation.Horizontal)
        threshold_slider.setRange(50, 95)
        threshold_slider.setTickInterval(5)
        self._threshold_label = QLabel("0.80")
        self._threshold_label.setFixedWidth(36)
        self._threshold_label.setStyleSheet("color: #888780; font-size: 11px;")
        threshold_slider.valueChanged.connect(
            lambda v: self._threshold_label.setText(f"{v/100:.2f}")
        )
        threshold_container = QWidget()
        threshold_container.setFixedWidth(200)
        tc_layout = QHBoxLayout(threshold_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.addWidget(threshold_slider)
        tc_layout.addWidget(self._threshold_label)
        self._controls["wake_threshold"] = threshold_slider
        form.addWidget(SettingRow(
            "Sensitivity",
            threshold_container,
            "Higher = less sensitive (fewer false triggers)"
        ))

        # ── Voice section ─────────────────────────────────────────────────────
        form.addSpacing(8)
        form.addWidget(SectionHeader("Voice"))
        form.addWidget(self._divider())

        voice_combo = QComboBox()
        voice_combo.addItems([
            "en-US-BrianNeural",
            "en-US-JennyNeural",
            "en-GB-RyanNeural",
            "en-GB-SoniaNeural",
            "en-AU-WilliamNeural",
            "en-IN-NeerjaNeural",
        ])
        self._controls["tts_voice"] = voice_combo
        form.addWidget(SettingRow(
            "TTS voice",
            voice_combo,
            "Microsoft neural voice for responses"
        ))

        rate_spin = QSpinBox()
        rate_spin.setRange(-50, 50)
        rate_spin.setSuffix("%")
        self._controls["tts_rate_int"] = rate_spin
        form.addWidget(SettingRow(
            "Speech rate",
            rate_spin,
            "Adjust speaking speed (0 = default)"
        ))

        # ── Speech Recognition section ────────────────────────────────────────
        form.addSpacing(8)
        form.addWidget(SectionHeader("Speech Recognition"))
        form.addWidget(self._divider())

        whisper_combo = QComboBox()
        whisper_combo.addItems(["tiny.en", "base.en", "small.en", "medium.en"])
        self._controls["whisper_model"] = whisper_combo
        form.addWidget(SettingRow(
            "Whisper model",
            whisper_combo,
            "Larger = more accurate, slower to load"
        ))

        silence_spin = QDoubleSpinBox()
        silence_spin.setRange(0.3, 3.0)
        silence_spin.setSingleStep(0.1)
        silence_spin.setSuffix("s")
        self._controls["stt_max_silence_sec"] = silence_spin
        form.addWidget(SettingRow(
            "Silence cutoff",
            silence_spin,
            "Stop recording after this much silence"
        ))

        # ── System section ────────────────────────────────────────────────────
        form.addSpacing(8)
        form.addWidget(SectionHeader("System"))
        form.addWidget(self._divider())

        battery_spin = QSpinBox()
        battery_spin.setRange(5, 50)
        battery_spin.setSuffix("%")
        self._controls["battery_warn_pct"] = battery_spin
        form.addWidget(SettingRow(
            "Battery warning",
            battery_spin,
            "Warn when battery drops below this"
        ))

        shutdown_spin = QSpinBox()
        shutdown_spin.setRange(1, 60)
        shutdown_spin.setSuffix("s")
        self._controls["shutdown_delay_sec"] = shutdown_spin
        form.addWidget(SettingRow(
            "Shutdown delay",
            shutdown_spin,
            "Seconds before shutdown executes"
        ))

        screenshot_input = QLineEdit()
        screenshot_input.setPlaceholderText("Default: ~/Pictures/Numa/Screenshots")
        self._controls["screenshot_folder"] = screenshot_input
        form.addWidget(SettingRow(
            "Screenshot folder",
            screenshot_input,
            "Leave blank for default location"
        ))

        # ── AI section ────────────────────────────────────────────────────────
        form.addSpacing(8)
        form.addWidget(SectionHeader("AI Model"))
        form.addWidget(self._divider())

        model_combo = QComboBox()
        model_combo.addItems([
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ])
        self._controls["llm_model"] = model_combo
        form.addWidget(SettingRow(
            "Gemini model",
            model_combo,
            "flash-lite = highest free quota"
        ))

        context_spin = QSpinBox()
        context_spin.setRange(2, 20)
        context_spin.setSuffix(" msgs")
        self._controls["llm_context_messages"] = context_spin
        form.addWidget(SettingRow(
            "Context window",
            context_spin,
            "Recent messages sent to Gemini"
        ))

        form.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

        # ── Footer with buttons ────────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(64)
        footer.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-top: 1px solid #D3D1C7;
            }
        """)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(24, 0, 24, 0)
        f_layout.setSpacing(12)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #A32D2D; font-size: 12px;")
        self._error_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        reset_btn = QPushButton("Reset defaults")
        reset_btn.setObjectName("reset")
        reset_btn.clicked.connect(self._reset_defaults)

        save_btn = QPushButton("Save changes")
        save_btn.setObjectName("save")
        save_btn.clicked.connect(self._save)

        f_layout.addWidget(self._error_label)
        f_layout.addWidget(reset_btn)
        f_layout.addWidget(save_btn)
        root.addWidget(footer)

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #D3D1C7;")
        return line

    # ── Value loading ─────────────────────────────────────────────────────────

    def _load_values(self):
        """Populate all controls from current settings."""
        def set_combo(key: str, widget: QComboBox):
            val = settings.get(key, "")
            idx = widget.findText(str(val))
            if idx >= 0:
                widget.setCurrentIndex(idx)

        set_combo("tts_voice",    self._controls["tts_voice"])
        set_combo("whisper_model",self._controls["whisper_model"])
        set_combo("llm_model",    self._controls["llm_model"])

        self._controls["wake_word"].setText(settings.get("wake_word", "alexa"))

        threshold = settings.get("wake_threshold", 0.8)
        self._controls["wake_threshold"].setValue(int(threshold * 100))
        self._threshold_label.setText(f"{threshold:.2f}")

        # TTS rate: "+5%" -> 5
        rate_str = settings.get("tts_rate", "+0%").replace("+", "").replace("%", "")
        try:
            self._controls["tts_rate_int"].setValue(int(rate_str))
        except ValueError:
            self._controls["tts_rate_int"].setValue(0)

        self._controls["stt_max_silence_sec"].setValue(
            settings.get("stt_max_silence_sec", 0.8)
        )
        self._controls["battery_warn_pct"].setValue(
            settings.get("battery_warn_pct", 15)
        )
        self._controls["shutdown_delay_sec"].setValue(
            settings.get("shutdown_delay_sec", 5)
        )
        self._controls["screenshot_folder"].setText(
            settings.get("screenshot_folder", "")
        )
        self._controls["llm_context_messages"].setValue(
            settings.get("llm_context_messages", 6)
        )

    # ── Save & Reset ──────────────────────────────────────────────────────────

    def _save(self):
        """Validate and persist all settings."""
        errors = []

        def save_one(key: str, value):
            ok, err = settings.set(key, value)
            if not ok:
                errors.append(f"{key}: {err}")

        save_one("wake_word",
                 self._controls["wake_word"].text().strip().lower())

        save_one("wake_threshold",
                 self._controls["wake_threshold"].value() / 100.0)

        save_one("tts_voice",
                 self._controls["tts_voice"].currentText())

        # TTS rate: int -> "+5%"
        rate_int = self._controls["tts_rate_int"].value()
        rate_str = f"+{rate_int}%" if rate_int >= 0 else f"{rate_int}%"
        save_one("tts_rate", rate_str)

        save_one("whisper_model",
                 self._controls["whisper_model"].currentText())

        save_one("stt_max_silence_sec",
                 self._controls["stt_max_silence_sec"].value())

        save_one("battery_warn_pct",
                 self._controls["battery_warn_pct"].value())

        save_one("shutdown_delay_sec",
                 self._controls["shutdown_delay_sec"].value())

        save_one("screenshot_folder",
                 self._controls["screenshot_folder"].text().strip())

        save_one("llm_model",
                 self._controls["llm_model"].currentText())

        save_one("llm_context_messages",
                 self._controls["llm_context_messages"].value())

        if errors:
            self._error_label.setText(errors[0])
            return

        self._error_label.setText("")
        numa_signals.settings_saved.emit()

    def _reset_defaults(self):
        """Reset all settings to factory defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to factory defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            settings.reset_to_defaults()
            self._load_values()
            self._error_label.setText("")
            numa_signals.settings_saved.emit()

    def closeEvent(self, event):
        """Hide instead of destroy."""
        event.ignore()
        self.hide()
