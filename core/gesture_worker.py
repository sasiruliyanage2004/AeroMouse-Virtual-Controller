import cv2
import time
import threading
from typing import Optional
from core.camera_manager import CameraManager
from core.gesture_engine import GestureEngine
from core.action_controller import ActionController
from core.events import Event, EventType
from core.event_bus import EventBus

class GestureWorker(threading.Thread):
    def __init__(self, status_callback=None, bus: Optional[EventBus] = None):
        super().__init__()
        self.running = True
        self.is_sleeping = True 
        self.status_callback = status_callback
        self.bus = bus
        self.daemon = True 
        
    def _emit_status(self, msg, state="SLEEPING", hand=""):
        print(msg)
        if self.status_callback:
            self.status_callback(msg)
        if self.bus:
            self.bus.publish(Event(
                event_type=EventType.GESTURE_STATE_CHANGED,
                payload={"state": state, "hand": hand, "message": msg},
                source="gesture_worker"
            ))
            
    def run(self):
        self._emit_status("Initializing Camera...")
        
        try:
            camera = CameraManager(camera_index=0)
            engine = GestureEngine()
            controller = ActionController() if self.bus is None else None
        except Exception as e:
            self._emit_status(f"Startup Error: {e}", state="ERROR")
            return

        if not camera.start():
            self._emit_status("Error: Could not open camera.", state="ERROR")
            return

        self._emit_status("SLEEPING (Thumbs Up to Wake)", state="SLEEPING")
        last_toggle_time = time.time()
        
        while self.running:
            try:
                ret, frame = camera.get_frame()
                if not ret:
                    time.sleep(0.1)
                    continue
                    
                processed_frame, action = engine.process_frame(frame)
                
                if action:
                    act_type, val = action
                    
                    # Toggle Wake/Sleep state and handle Hand Locking
                    if act_type == 'toggle_state':
                        if time.time() - last_toggle_time > 2.0:
                            engine.is_sleeping = not engine.is_sleeping
                            self.is_sleeping = engine.is_sleeping
                            
                            if self.is_sleeping:
                                engine.locked_handedness = None
                                self._emit_status("SLEEPING (Thumbs Up to Wake)", state="SLEEPING")
                            else:
                                engine.locked_handedness = val
                                self._emit_status(f"ACTIVE (Locked to {val} Hand)", state="ACTIVE", hand=val)
                            
                            last_toggle_time = time.time()
                            
                    # Dispatch actions only if ACTIVE
                    elif not self.is_sleeping:
                        if self.bus:
                            # Non-blocking EventBus dispatch
                            if act_type == 'move':
                                self.bus.publish(Event(event_type=EventType.GESTURE_POINTER_MOVE, payload={"coords": val}))
                            elif act_type == 'click':
                                self.bus.publish(Event(event_type=EventType.GESTURE_CLICK, payload={"button": "left"}))
                            elif act_type == 'scroll':
                                self.bus.publish(Event(event_type=EventType.GESTURE_SCROLL, payload={"delta": val}))
                            elif act_type in ['minimize_window', 'maximize_window', 'close_window']:
                                self.bus.publish(Event(event_type=EventType.GESTURE_DETECTED, payload={"action": act_type}))
                        else:
                            # Direct execution fallback for standalone backward compatibility
                            if act_type == 'move':
                                controller.move_to(val[0], val[1])
                            elif act_type == 'click':
                                controller.click()
                            elif act_type == 'scroll':
                                controller.scroll(val)
                            elif act_type == 'minimize_window':
                                controller.minimize_window()
                            elif act_type == 'maximize_window':
                                controller.maximize_window()
                            elif act_type == 'close_window':
                                controller.close_window()
                
                # CPU throttling
                if self.is_sleeping:
                    time.sleep(0.08) 
                else:
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"[GestureWorker Recovery]: {e}")
                time.sleep(0.5)
                
        try:
            camera.stop()
            engine.release()
        except Exception:
            pass

    def stop(self):
        self.running = False
