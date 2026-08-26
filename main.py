import cv2
import time
from core.camera_manager import CameraManager
from core.gesture_engine import GestureEngine
from core.action_controller import ActionController

def main():
    print("Initializing Virtual Mouse App...")
    
    camera = CameraManager(camera_index=0)
    engine = GestureEngine()
    controller = ActionController()
    
    if not camera.start():
        print("Error: Could not open camera.")
        return

    print("Virtual Mouse is ACTIVE!")
    print("- Move: Point Index finger")
    print("- Click: Pinch Index & Thumb")
    print("- Scroll: Index & Middle up")
    print("- Minimize: Make a Fist")
    print("- Maximize: Open Hand (All fingers up)")
    print("- Close App: Show Pinky only")
    print("Press 'q' on the video window to quit.")
    
    try:
        while True:
            ret, frame = camera.get_frame()
            if not ret:
                break
                
            processed_frame, action = engine.process_frame(frame)
            
            if action:
                act_type, val = action
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
                    
            cv2.imshow("Gesture Control - AI Vision", processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        camera.stop()
        engine.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
