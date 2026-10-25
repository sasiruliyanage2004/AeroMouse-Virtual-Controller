import time
import math
import ctypes
import threading
import queue
from typing import Optional
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
from core.events import Event, EventType
from core.event_bus import EventBus

class ActionExecutor:
    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or EventBus()
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        user32 = ctypes.windll.user32
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)
        
        # State tracking
        self.prev_x = self.screen_width // 2
        self.prev_y = self.screen_height // 2
        self.last_click_time = 0.0
        self.last_action_time = 0.0
        self.scroll_speed = 3
        
        # Dead zone to eliminate pointer micro-jitter
        self.dead_zone_px = 3.0
        
        # Threaded queue for non-blocking serialized OS actions
        self._action_queue = queue.Queue(maxsize=100)
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._process_actions,
            name="ActionExecutorThread",
            daemon=True
        )
        
        self._register_subscriptions()
        self._worker_thread.start()

    def _register_subscriptions(self):
        self.bus.subscribe(EventType.GESTURE_POINTER_MOVE, self._on_pointer_event)
        self.bus.subscribe(EventType.GESTURE_CLICK, self._on_click_event)
        self.bus.subscribe(EventType.GESTURE_SCROLL, self._on_scroll_event)
        self.bus.subscribe(EventType.GESTURE_DETECTED, self._on_gesture_event)

    def _on_pointer_event(self, event: Event):
        coords = event.payload.get("coords")
        if coords:
            # Drop older pointer moves if executor is saturated
            if self._action_queue.full():
                try: self._action_queue.get_nowait()
                except queue.Empty: pass
            self._action_queue.put_nowait(("move", coords))

    def _on_click_event(self, event: Event):
        button = event.payload.get("button", "left")
        self._action_queue.put(("click", button))

    def _on_scroll_event(self, event: Event):
        delta = event.payload.get("delta", 0)
        self._action_queue.put(("scroll", delta))

    def _on_gesture_event(self, event: Event):
        action_name = event.payload.get("action")
        if action_name in ["minimize_window", "maximize_window", "close_window"]:
            self._action_queue.put((action_name, None))

    def _process_actions(self):
        while self._running:
            try:
                action, data = self._action_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                if action == "move":
                    self._execute_move(data[0], data[1])
                elif action == "click":
                    self._execute_click(data)
                elif action == "scroll":
                    self._execute_scroll(data)
                elif action == "minimize_window":
                    self._execute_minimize()
                elif action == "maximize_window":
                    self._execute_maximize()
                elif action == "close_window":
                    self._execute_close()
            except Exception as e:
                print(f"[ActionExecutor Error]: {e}")
                
            self._action_queue.task_done()

    def _execute_move(self, x_ratio: float, y_ratio: float):
        margin = 0.15
        norm_x = (x_ratio - margin) / (1.0 - 2.0 * margin)
        norm_y = (y_ratio - margin) / (1.0 - 2.0 * margin)
        
        clamped_x = max(0.0, min(1.0, norm_x))
        clamped_y = max(0.0, min(1.0, norm_y))
        
        target_x = int(clamped_x * self.screen_width)
        target_y = int(clamped_y * self.screen_height)
        
        # Dead-zone calculation
        dist = math.hypot(target_x - self.prev_x, target_y - self.prev_y)
        if dist < self.dead_zone_px:
            return # Ignore micro-tremors for button stability
            
        # Velocity-adaptive smoothing
        if dist < 25:
            smooth_factor = 0.20 # High precision for tiny targets
        elif dist < 120:
            smooth_factor = 0.40 # Standard movement
        else:
            smooth_factor = 0.65 # Fast tracking across displays
            
        curr_x = int(self.prev_x + (target_x - self.prev_x) * smooth_factor)
        curr_y = int(self.prev_y + (target_y - self.prev_y) * smooth_factor)
        
        try:
            self.mouse.position = (curr_x, curr_y)
        except Exception:
            pass
            
        self.prev_x = curr_x
        self.prev_y = curr_y

    def _execute_click(self, button_name: str = "left"):
        now = time.time()
        if now - self.last_click_time > 0.35: # Debounce protection
            try:
                btn = Button.left if button_name == "left" else Button.right
                self.mouse.click(btn)
                print(f"[ActionExecutor] {button_name.capitalize()} click executed.")
            except Exception as e:
                print(f"[ActionExecutor] Click error: {e}")
            self.last_click_time = now

    def _execute_scroll(self, delta: int):
        try:
            self.mouse.scroll(0, delta * self.scroll_speed)
        except Exception:
            pass

    def _execute_minimize(self):
        now = time.time()
        if now - self.last_action_time > 1.5:
            try:
                with self.keyboard.pressed(Key.cmd):
                    self.keyboard.press(Key.down)
                    self.keyboard.release(Key.down)
                print("[ActionExecutor] Window minimized.")
            except Exception:
                pass
            self.last_action_time = now

    def _execute_maximize(self):
        now = time.time()
        if now - self.last_action_time > 1.5:
            try:
                with self.keyboard.pressed(Key.cmd):
                    self.keyboard.press(Key.up)
                    self.keyboard.release(Key.up)
                print("[ActionExecutor] Window maximized.")
            except Exception:
                pass
            self.last_action_time = now

    def _execute_close(self):
        now = time.time()
        if now - self.last_action_time > 2.0:
            try:
                with self.keyboard.pressed(Key.alt):
                    self.keyboard.press(Key.f4)
                    self.keyboard.release(Key.f4)
                print("[ActionExecutor] Window closed.")
            except Exception:
                pass
            self.last_action_time = now

    def stop(self):
        self._running = False
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
