import os
import time
import asyncio
import ctypes
import tempfile
import edge_tts
import sounddevice as sd
import numpy as np
import wave
from agent.config import VOICE_NAME

class VoiceEngine:
    def __init__(self, voice_name=VOICE_NAME):
        self.voice_name = voice_name
        self.sample_rate = 16000
        self.mci = ctypes.windll.winmm.mciSendStringW

    def speak(self, text: str):
        """
        Converts text to speech using Edge-TTS and plays it seamlessly in the background.
        """
        if not text or not text.strip():
            return
            
        print(f"SAS: {text}")
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_filename = fp.name

            # Generate natural AI audio file
            communicate = edge_tts.Communicate(text, self.voice_name)
            asyncio.run(communicate.save(temp_filename))

            # Play audio using native Windows Media Control Interface (no popup windows)
            alias = f"sas_audio_{int(time.time() * 1000)}"
            self.mci(f'open "{temp_filename}" type mpegvideo alias {alias}', None, 0, None)
            self.mci(f'play {alias} wait', None, 0, None)
            self.mci(f'close {alias}', None, 0, None)

            # Cleanup temp file
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception:
                    pass
        except Exception as e:
            print(f"TTS Error: {e}")

    def record_audio(self, duration_sec: int = 5) -> str:
        """
        Records audio from the user's microphone for duration_sec seconds
        and returns the path to the recorded WAV file.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
            wav_path = fp.name

        try:
            print("Listening...")
            audio_data = sd.rec(
                int(duration_sec * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())
                
            return wav_path
        except Exception as e:
            print(f"Microphone recording error: {e}")
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return None
