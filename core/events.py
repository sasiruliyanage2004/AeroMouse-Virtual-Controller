import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional

class EventPriority(Enum):
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()

class EventType(Enum):
    # Vision & Gesture Events
    GESTURE_DETECTED = "gesture.detected"
    GESTURE_POINTER_MOVE = "gesture.pointer_move"
    GESTURE_CLICK = "gesture.click"
    GESTURE_SCROLL = "gesture.scroll"
    GESTURE_STATE_CHANGED = "gesture.state_changed"
    
    # Audio & Voice Events
    WAKE_WORD_DETECTED = "audio.wake_word"
    SPEECH_LISTENING_START = "audio.listening_start"
    SPEECH_LISTENING_END = "audio.listening_end"
    SPEECH_TRANSCRIBED = "audio.transcribed"
    TTS_SPEAKING_START = "audio.tts_start"
    TTS_SPEAKING_END = "audio.tts_end"
    
    # Agent & Tool Events
    AGENT_COMMAND_RECEIVED = "agent.command_received"
    AGENT_TOOL_CALLING = "agent.tool_calling"
    AGENT_TOOL_EXECUTED = "agent.tool_executed"
    AGENT_RESPONSE_READY = "agent.response_ready"
    AGENT_CONFIRMATION_REQUIRED = "agent.confirmation_required"
    
    # Screen Perception Events
    SCREEN_CAPTURED = "screen.captured"
    SCREEN_WINDOW_CHANGED = "screen.window_changed"
    
    # System & Lifecycle Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_STATUS = "system.status"
    SYSTEM_ERROR = "system.error"

@dataclass
class Event:
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    priority: EventPriority = EventPriority.NORMAL
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.event_id,
            "type": self.event_type.value,
            "source": self.source,
            "priority": self.priority.name,
            "timestamp": self.timestamp,
            "payload": self.payload
        }
