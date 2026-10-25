# SAS - Smart Autonomous System Configuration
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
WAKE_WORD = "sas"
ASSISTANT_NAME = "SAS"
VOICE_NAME = "en-US-ChristopherNeural"  # Professional AI assistant voice
