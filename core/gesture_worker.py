import cv2
import time
import threading
from core.camera_manager import CameraManager
from core.gesture_engine import GestureEngine
from core.action_controller import ActionController

class GestureWorker(threading.Thread):
    def __init__(self, status_callback=None):
        super().__init__()
        self.running = True
        self.is_sleeping = True 
        self.status_callback = status_callback
        self.daemon = True # Allows script to exit safely
        
    def _emit_status(self, msg):
        print(msg)
        if self.status_callback:
            self.status_callback(msg)
            
    def run(self):
        self._emit_status("Initializing Camera...")
        camera = CameraManager(camera_index=0)
        engine = GestureEngine()
        controller = ActionController()
        
        if not camera.start():
            self._emit_status("Error: Could not open camera.")
            return

        self._emit_status("SLEEPING (Thumbs Up to Wake)")
        last_toggle_time = time.time()
        
        while self.running:
            ret, frame = camera.get_frame()
            if not ret:
                continue
                
            processed_frame, action = engine.process_frame(frame)
            
            if action:
                act_type, val = action
                
                # Toggle Wake/Sleep state
                if act_type == 'toggle_state':
                    if time.time() - last_toggle_time > 2.0:
                        self.is_sleeping = not self.is_sleeping
                        if self.is_sleeping:
                            self._emit_status("SLEEPING (Thumbs Up to Wake)")
                        else:
                            self._emit_status("ACTIVE (Thumbs Up to Sleep)")
                        last_toggle_time = time.time()
                        
                # Execute OS actions only if ACTIVE
                elif not self.is_sleeping:
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
            
            if self.is_sleeping:
                time.sleep(0.1) 
            else:
                time.sleep(0.01)
                
        camera.stop()
        engine.release()

    def stop(self):
        self.running = False
