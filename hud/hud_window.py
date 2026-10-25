import sys
import time
from typing import Optional
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject
from core.events import Event, EventType
from core.event_bus import EventBus

class HUDEventBridge(QObject):
    """Bridges background EventBus events into the Qt GUI main thread safely."""
    status_updated = pyqtSignal(str, str) # title, detail
    gesture_updated = pyqtSignal(str)     # gesture state
    activity_logged = pyqtSignal(str)     # last action log

class SASHUDWindow(QtWidgets.QWidget):
    def __init__(self, bus: Optional[EventBus] = None):
        super().__init__()
        self.bus = bus or EventBus()
        self.bridge = HUDEventBridge()
        
        self.drag_position = QPoint()
        self._init_ui()
        self._connect_events()

    def _init_ui(self):
        # Frameless, Always-On-Top, Translucent Window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(360, 160)
        
        # Position at top-right corner of screen by default
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.move(screen.width() - 390, 40)

        # Main Layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Glassmorphic Card Container
        self.card = QtWidgets.QFrame(self)
        self.card.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 20, 35, 220);
                border: 1px solid rgba(0, 240, 255, 120);
                border-radius: 14px;
            }
        """)
        card_layout = QtWidgets.QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 12, 14, 12)

        # Header: SAS Identity & Status Pill
        header_layout = QtWidgets.QHBoxLayout()
        
        self.logo_label = QtWidgets.QLabel("🤖 SAS // AGENT", self.card)
        self.logo_label.setStyleSheet("""
            QLabel {
                color: #00F0FF;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
                font-size: 13px;
                letter-spacing: 1px;
                border: none;
                background: transparent;
            }
        """)
        header_layout.addWidget(self.logo_label)
        header_layout.addStretch()

        self.status_pill = QtWidgets.QLabel("ONLINE", self.card)
        self.status_pill.setStyleSheet("""
            QLabel {
                color: #00FF9D;
                background-color: rgba(0, 255, 157, 30);
                border: 1px solid #00FF9D;
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(self.status_pill)
        card_layout.addLayout(header_layout)

        # Middle Section: Gesture & Voice Status
        telemetry_layout = QtWidgets.QHBoxLayout()
        
        self.gesture_badge = QtWidgets.QLabel("🖐️ AeroMouse: STANDBY", self.card)
        self.gesture_badge.setStyleSheet("""
            QLabel {
                color: #A0C4E2;
                font-size: 11px;
                border: none;
                background: transparent;
            }
        """)
        telemetry_layout.addWidget(self.gesture_badge)
        telemetry_layout.addStretch()
        card_layout.addLayout(telemetry_layout)

        # Activity Terminal Bar (Shows latest executed action)
        self.action_label = QtWidgets.QLabel("Ready for touchless & voice commands.", self.card)
        self.action_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 11px;
                background-color: rgba(0, 0, 0, 80);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)
        self.action_label.setWordWrap(True)
        card_layout.addWidget(self.action_label)

        main_layout.addWidget(self.card)

    def _connect_events(self):
        # Connect bridge signals to slot updates
        self.bridge.status_updated.connect(self._update_status_ui)
        self.bridge.gesture_updated.connect(self._update_gesture_ui)
        self.bridge.activity_logged.connect(self._update_action_ui)

        # Subscribe bridge to EventBus
        self.bus.subscribe(EventType.GESTURE_STATE_CHANGED, self._handle_gesture_state)
        self.bus.subscribe(EventType.SPEECH_LISTENING_START, lambda e: self.bridge.status_updated.emit("LISTENING", "#FFB703"))
        self.bus.subscribe(EventType.SPEECH_LISTENING_END, lambda e: self.bridge.status_updated.emit("THINKING", "#9D4EDD"))
        self.bus.subscribe(EventType.TTS_SPEAKING_START, lambda e: self.bridge.status_updated.emit("SPEAKING", "#00F0FF"))
        self.bus.subscribe(EventType.TTS_SPEAKING_END, lambda e: self.bridge.status_updated.emit("ONLINE", "#00FF9D"))
        self.bus.subscribe(EventType.AGENT_RESPONSE_READY, lambda e: self.bridge.activity_logged.emit(f"SAS: {e.payload.get('reply', '')[:55]}..."))
        self.bus.subscribe(EventType.AGENT_COMMAND_RECEIVED, lambda e: self.bridge.activity_logged.emit(f"User: {e.payload.get('command', '')}"))

    def _handle_gesture_state(self, event: Event):
        state = event.payload.get("state", "STANDBY")
        hand = event.payload.get("hand", "")
        text = f"🖐️ AeroMouse: {state}"
        if hand:
            text += f" ({hand})"
        self.bridge.gesture_updated.emit(text)

    def _update_status_ui(self, status: str, color_hex: str):
        self.status_pill.setText(status)
        self.status_pill.setStyleSheet(f"""
            QLabel {{
                color: {color_hex};
                background-color: rgba(20, 20, 30, 180);
                border: 1px solid {color_hex};
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)

    def _update_gesture_ui(self, text: str):
        self.gesture_badge.setText(text)

    def _update_action_ui(self, text: str):
        self.action_label.setText(text)

    # Enable drag-and-drop window movement
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
