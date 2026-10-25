import os
import time
import ctypes
import tempfile
from typing import Dict, Any, Optional, Tuple
from PIL import ImageGrab
from core.events import Event, EventType
from core.event_bus import EventBus

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

class ScreenContextManager:
    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or EventBus()
        self.user32 = ctypes.windll.user32
        self.privacy_mode_enabled = False # If True, blocks screen capture

    def get_active_window_info(self) -> Dict[str, Any]:
        """
        Retrieves the handle, title, and screen coordinates of the active foreground window.
        """
        hwnd = self.user32.GetForegroundWindow()
        if not hwnd:
            return {"title": "Unknown", "hwnd": 0, "rect": None}

        # Get window title
        length = self.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value or "Untitled Window"

        # Get window bounding rectangle
        rect = RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        return {
            "title": title,
            "hwnd": hwnd,
            "rect": (rect.left, rect.top, rect.right, rect.bottom),
            "width": max(0, rect.right - rect.left),
            "height": max(0, rect.bottom - rect.top)
        }

    def capture_screen(self, active_window_only: bool = False) -> Optional[str]:
        """
        Captures a fresh screenshot of the active window or full desktop.
        Returns the temporary file path of the compressed image for LLM reasoning.
        """
        if self.privacy_mode_enabled:
            print("[ScreenContext] Screen capture blocked by Privacy Policy.")
            return None

        window_info = self.get_active_window_info()
        bbox = None
        
        if active_window_only and window_info["rect"]:
            l, t, r, b = window_info["rect"]
            if r > l and b > t:
                bbox = (l, t, r, b)

        try:
            # High-performance PIL capture
            img = ImageGrab.grab(bbox=bbox, all_screens=True if bbox is None else False)
            
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as fp:
                temp_path = fp.name

            # Compress slightly for fast network transmission
            img.save(temp_path, format="JPEG", quality=85)

            self.bus.publish(Event(
                event_type=EventType.SCREEN_CAPTURED,
                payload={
                    "window_title": window_info["title"],
                    "dimensions": (img.width, img.height),
                    "active_window_only": active_window_only
                },
                source="screen_context"
            ))

            return temp_path
        except Exception as e:
            print(f"[ScreenContext] Screen capture failed: {e}")
            return None
