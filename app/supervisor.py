import os
import time
import threading
from typing import Optional

from core.events import Event, EventType
from core.event_bus import EventBus
from core.gesture_worker import GestureWorker
from automation.action_executor import ActionExecutor
from perception.audio_worker import AudioWorker
from perception.screen_context import ScreenContextManager
from agent.brain import SASBrain

class SASSupervisor:
    """
    Central supervisor that manages the application lifecycle, workers,
    and event flows for SAS (Smart Autonomous System).
    """
    def __init__(self, enable_gestures: bool = True):
        self.bus = EventBus()
        self.enable_gestures = enable_gestures
        
        # Core Subsystems
        self.action_executor = ActionExecutor(bus=self.bus)
        self.screen_manager = ScreenContextManager(bus=self.bus)
        self.brain = SASBrain(bus=self.bus)
        
        # Audio Worker with VAD
        self.audio_worker = AudioWorker(
            bus=self.bus,
            on_speech_transcribed=self._on_speech_command
        )
        
        # Vision / Gesture Worker
        self.gesture_worker: Optional[GestureWorker] = None
        if self.enable_gestures:
            self.gesture_worker = GestureWorker(bus=self.bus)

        self._running = False

    def start(self):
        """Starts all background workers and announces readiness."""
        self._running = True
        self.bus.publish(Event(
            event_type=EventType.SYSTEM_STARTUP,
            payload={"version": "2.0", "status": "ONLINE"},
            source="supervisor"
        ))

        # Start Vision if enabled
        if self.gesture_worker:
            self.gesture_worker.start()

        # Voice greeting in background
        greeting = "SAS is online and ready. Voice and gesture controls are active."
        threading.Thread(
            target=self.audio_worker.speak,
            args=(greeting,),
            daemon=True
        ).start()

    def listen_and_process(self):
        """Triggers real-time VAD voice listening, transcribes, and executes command."""
        def _listen_task():
            transcription = self.audio_worker.capture_single_command(
                transcribe_fn=self.brain.transcribe_audio
            )
            if transcription:
                self._on_speech_command(transcription)
            else:
                self.audio_worker.speak("I didn't hear anything. Ready when you are.")

        threading.Thread(target=_listen_task, daemon=True).start()

    def _on_speech_command(self, user_command: str):
        """Dispatches recognized speech to the Brain and speaks the result."""
        def _execute_task():
            reply = self.brain.process_command(user_command)
            self.audio_worker.speak(reply)

        threading.Thread(target=_execute_task, daemon=True).start()

    def execute_text_command(self, text: str) -> str:
        """Processes a text command through SAS Brain and speaks the answer."""
        reply = self.brain.process_command(text)
        threading.Thread(
            target=self.audio_worker.speak,
            args=(reply,),
            daemon=True
        ).start()
        return reply

    def stop(self):
        """Gracefully shuts down all workers, releases devices and closes threads."""
        print("[Supervisor] Initiating graceful shutdown...")
        self._running = False
        
        self.bus.publish(Event(
            event_type=EventType.SYSTEM_SHUTDOWN,
            source="supervisor"
        ))

        if self.gesture_worker:
            self.gesture_worker.stop()

        self.audio_worker.stop()
        self.action_executor.stop()
        self.bus.stop()
        print("[Supervisor] Shutdown complete.")
