import os
import dotenv
from typing import Optional
from google import genai
from google.genai import types

from agent.config import GEMINI_API_KEY
from core.events import Event, EventType
from core.event_bus import EventBus
from security.policy_engine import SecurityPolicyEngine

# Tool imports
from agent.tools.email_tool import send_or_compose_email
from agent.tools.screen_tool import inspect_active_screen
from agent.tools.system_tool import (
    launch_application,
    open_website,
    search_web,
    play_youtube,
    control_volume,
    lock_workstation,
    get_current_time_date
)

class SASBrain:
    def __init__(self, api_key: Optional[str] = None, bus: Optional[EventBus] = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")
            
        self.bus = bus or EventBus()
        self.policy_engine = SecurityPolicyEngine(require_confirmation_for_consequential=False)
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3.5-flash-lite"
        
        # Tools provided to SAS with Automatic Function Calling
        self.tools = [
            send_or_compose_email,
            inspect_active_screen,
            launch_application,
            open_website,
            search_web,
            play_youtube,
            control_volume,
            lock_workstation,
            get_current_time_date
        ]
        
        self.system_instruction = (
            "You are SAS (Smart Autonomous System), an intelligent, highly capable AI desktop assistant "
            "running on Windows with autonomous computer control and screen perception capabilities.\n"
            "You have direct access to system tools to execute user commands.\n"
            "Rules:\n"
            "1. When the user asks you to do something (e.g., 'send email to ...', 'open Chrome', 'play music on YouTube', "
            "'what's on my screen', 'summarize this document', 'what time is it', 'lock my PC', 'mute volume'), ALWAYS call the appropriate tool.\n"
            "2. Keep your conversational responses concise, clear, and professional, like a real AI assistant (JARVIS style).\n"
            "3. If the user speaks in Sinhala, understand the intent and respond naturally in Sinhala or friendly English."
        )
        
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                tools=self.tools,
                system_instruction=self.system_instruction,
                temperature=0.3
            )
        )

    def process_command(self, user_text: str) -> str:
        """
        Processes a user text command through Gemini's Automatic Function Calling loop,
        publishing lifecycle events to the EventBus.
        """
        if not user_text or not user_text.strip():
            return "I didn't catch that. Could you repeat?"

        print(f"\n[User Command]: {user_text}")
        self.bus.publish(Event(
            event_type=EventType.AGENT_COMMAND_RECEIVED,
            payload={"command": user_text},
            source="sas_brain"
        ))

        try:
            response = self.chat.send_message(user_text)
            reply_text = response.text or "Command executed successfully."
            
            self.bus.publish(Event(
                event_type=EventType.AGENT_RESPONSE_READY,
                payload={"reply": reply_text},
                source="sas_brain"
            ))
            return reply_text
        except Exception as e:
            err_msg = f"An error occurred while executing the command: {e}"
            print(f"[SAS Brain Error]: {e}")
            self.bus.publish(Event(
                event_type=EventType.SYSTEM_ERROR,
                payload={"error": str(e)},
                source="sas_brain"
            ))
            return err_msg

    def transcribe_audio(self, wav_file_path: str) -> str:
        """
        Transcribes recorded audio using Gemini's multimodal audio perception.
        """
        if not wav_file_path or not os.path.exists(wav_file_path):
            return ""
            
        try:
            with open(wav_file_path, "rb") as f:
                audio_bytes = f.read()

            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            prompt = "Transcribe the exact words spoken by the user in this audio. Output only the transcription, nothing else."
            
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=[audio_part, prompt]
            )
            transcription = res.text.strip() if res.text else ""
            return transcription
        except Exception as e:
            print(f"[Transcription Error]: {e}")
            return ""
