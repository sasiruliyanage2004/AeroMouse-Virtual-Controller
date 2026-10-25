import os
import time
import math
import wave
import tempfile
import threading
from collections import deque
from typing import Optional, Callable
import sounddevice as sd
import numpy as np
from core.events import Event, EventType
from core.event_bus import EventBus
from agent.voice_engine import VoiceEngine

class AudioWorker:
    def __init__(self, bus: Optional[EventBus] = None, on_speech_transcribed: Optional[Callable[[str], None]] = None):
        self.bus = bus or EventBus()
        self.on_speech_transcribed = on_speech_transcribed
        self.voice_engine = VoiceEngine()
        
        self.sample_rate = 16000
        self.chunk_duration = 0.1 # 100ms chunks
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)
        
        # VAD Parameters
        self.silence_threshold_rms = 450.0  # Dynamic baseline energy
        self.silence_duration_limit = 1.0   # 1 second of silence marks end-of-speech
        self.max_speech_duration = 10.0     # 10s max command limit
        self.pre_roll_chunks = 4            # 400ms pre-roll buffer
        
        self.is_listening = False
        self._running = True
        self._is_speaking = False
        self._audio_thread = None

    def start_listening_loop(self):
        """Starts background thread waiting for speech trigger."""
        self._audio_thread = threading.Thread(
            target=self._vad_stream_worker,
            name="AudioWorkerVAD",
            daemon=True
        )
        self._audio_thread.start()

    def capture_single_command(self, transcribe_fn: Optional[Callable[[str], str]] = None) -> Optional[str]:
        """
        Actively listens with real-time VAD until the user speaks and pauses.
        Returns the transcribed text string without requiring fixed 5s waits.
        """
        self.bus.publish(Event(
            event_type=EventType.SPEECH_LISTENING_START,
            source="audio_worker"
        ))
        
        print("[AudioWorker] Listening... (speak now)")
        pre_roll = deque(maxlen=self.pre_roll_chunks)
        recorded_frames = []
        speech_started = False
        silence_start_time = None
        start_time = time.time()
        
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16') as stream:
                while self._running:
                    chunk, overflow = stream.read(self.chunk_samples)
                    chunk_data = chunk.flatten()
                    
                    # Compute chunk RMS energy
                    rms = np.sqrt(np.mean(chunk_data.astype(np.float32) ** 2))
                    
                    if not speech_started:
                        pre_roll.append(chunk_data)
                        if rms > self.silence_threshold_rms:
                            speech_started = True
                            print("[AudioWorker] Speech detected! Recording...")
                            # Flush pre-roll buffer so we don't clip the first syllable
                            for pr_chunk in pre_roll:
                                recorded_frames.append(pr_chunk)
                    else:
                        recorded_frames.append(chunk_data)
                        if rms < self.silence_threshold_rms:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            elif time.time() - silence_start_time > self.silence_duration_limit:
                                print("[AudioWorker] Speech ended (silence detected).")
                                break
                        else:
                            silence_start_time = None # Reset silence counter if user resumes talking
                            
                    # Timeout guard
                    if time.time() - start_time > self.max_speech_duration:
                        print("[AudioWorker] Max recording duration reached.")
                        break
        except Exception as e:
            print(f"[AudioWorker Recording Error]: {e}")
            return None

        self.bus.publish(Event(
            event_type=EventType.SPEECH_LISTENING_END,
            source="audio_worker"
        ))

        if not recorded_frames:
            print("[AudioWorker] No speech captured.")
            return None

        # Assemble audio into a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
            wav_path = fp.name

        try:
            all_audio = np.concatenate(recorded_frames)
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(all_audio.tobytes())

            # Transcribe
            transcription = ""
            if transcribe_fn:
                transcription = transcribe_fn(wav_path)
            
            if transcription:
                self.bus.publish(Event(
                    event_type=EventType.SPEECH_TRANSCRIBED,
                    payload={"text": transcription},
                    source="audio_worker"
                ))
                if self.on_speech_transcribed:
                    self.on_speech_transcribed(transcription)

            return transcription
        finally:
            if os.path.exists(wav_path):
                try: os.remove(wav_path)
                except Exception: pass

    def speak(self, text: str):
        """Speaks through VoiceEngine and emits lifecycle events."""
        if not text or not text.strip():
            return
            
        self._is_speaking = True
        self.bus.publish(Event(
            event_type=EventType.TTS_SPEAKING_START,
            payload={"text": text},
            source="audio_worker"
        ))
        
        try:
            self.voice_engine.speak(text)
        finally:
            self._is_speaking = False
            self.bus.publish(Event(
                event_type=EventType.TTS_SPEAKING_END,
                payload={"text": text},
                source="audio_worker"
            ))

    def stop(self):
        self._running = False
