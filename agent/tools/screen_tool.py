import os
from typing import Optional
from google.genai import types
from perception.screen_context import ScreenContextManager

_screen_mgr = ScreenContextManager()

def inspect_active_screen(question: str = "Describe what is currently visible on the screen.") -> str:
    """
    Captures the user's active computer screen and uses visual reasoning to answer questions about it.
    Use this tool whenever the user asks:
    - 'What's on my screen right now?'
    - 'Summarize this document/window/page'
    - 'Explain the error code visible on my screen'
    - 'Read the text in the active window'
    """
    img_path = _screen_mgr.capture_screen(active_window_only=False)
    if not img_path:
        return "Screen capture was not possible or was blocked by privacy policy."

    try:
        # Import SASBrain client safely
        from agent.config import GEMINI_API_KEY
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        with open(img_path, "rb") as f:
            img_bytes = f.read()

        image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        prompt = (
            f"You are SAS, an intelligent desktop assistant with screen awareness.\n"
            f"The user is asking: '{question}'\n"
            f"Carefully analyze this fresh screenshot of the user's desktop screen and answer accurately and concisely."
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[image_part, prompt]
        )
        return response.text or "I inspected the screen but could not discern specific details."
    except Exception as e:
        return f"Error analyzing screen: {e}"
    finally:
        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass
