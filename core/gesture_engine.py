import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import os

class GestureEngine:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.prev_y = None
        
    def process_frame(self, frame):
        action = None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        detection_result = self.detector.detect(mp_image)

        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                h, w, c = frame.shape
                
                # To make finger detection much more stable, we check if the tip is 
                # above BOTH the PIP joint and the MCP (base) joint.
                is_index_up = hand_landmarks[8].y < hand_landmarks[6].y and hand_landmarks[8].y < hand_landmarks[5].y
                is_middle_up = hand_landmarks[12].y < hand_landmarks[10].y and hand_landmarks[12].y < hand_landmarks[9].y
                is_ring_up = hand_landmarks[16].y < hand_landmarks[14].y and hand_landmarks[16].y < hand_landmarks[13].y
                is_pinky_up = hand_landmarks[20].y < hand_landmarks[18].y and hand_landmarks[20].y < hand_landmarks[17].y
                
                is_index_down = not is_index_up
                is_middle_down = not is_middle_up
                is_ring_down = not is_ring_up
                is_pinky_down = not is_pinky_up
                
                # Thumbs up: Thumb is high, other fingers are definitely folded down
                is_thumb_up_only = (hand_landmarks[4].y < hand_landmarks[5].y) and is_index_down and is_middle_down and is_ring_down
                
                # Fist: All fingers down (excluding thumb for easier fisting)
                is_fist = is_index_down and is_middle_down and is_ring_down and is_pinky_down and not is_thumb_up_only
                
                # Open Hand: All fingers up
                is_open_hand = is_index_up and is_middle_up and is_ring_up and is_pinky_up
                
                index_x = hand_landmarks[8].x
                index_y = hand_landmarks[8].y
                
                # Calculate pinch distance (Index and Thumb)
                pinch_dist = math.hypot(hand_landmarks[8].x - hand_landmarks[4].x, 
                                        hand_landmarks[8].y - hand_landmarks[4].y)
                
                # Visual feedback for pinch
                if pinch_dist < 0.08:
                    x1, y1 = int(hand_landmarks[8].x * w), int(hand_landmarks[8].y * h)
                    x2, y2 = int(hand_landmarks[4].x * w), int(hand_landmarks[4].y * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

                # 1. Prioritize Wake/Sleep Toggle Gesture
                if is_thumb_up_only:
                    action = ('toggle_state', None)
                
                # 2. Minimize Window
                elif is_fist:
                    action = ('minimize_window', None)
                    
                # 3. Maximize Window
                elif is_open_hand:
                    action = ('maximize_window', None)
                    
                # 4. Scroll (We relax this: just need Index and Middle UP. We ignore Ring and Pinky to stop glitching)
                elif is_index_up and is_middle_up:
                    index_tip_y = int(index_y * h)
                    if self.prev_y is not None:
                        delta = self.prev_y - index_tip_y
                        if delta > 15:
                            action = ('scroll', 1)
                            self.prev_y = index_tip_y
                        elif delta < -15:
                            action = ('scroll', -1)
                            self.prev_y = index_tip_y
                    else:
                        self.prev_y = index_tip_y
                        
                # 5. Click
                elif pinch_dist < 0.08:
                    action = ('click', None)
                    self.prev_y = None
                    
                # 6. Move Mouse (We relax this: just need Index UP, Middle DOWN. Ignore Ring and Pinky to stop glitching)
                elif is_index_up and is_middle_down:
                    self.prev_y = None
                    action = ('move', (index_x, index_y))
                else:
                    self.prev_y = None 
        else:
            self.prev_y = None

        return frame, action

    def release(self):
        self.detector.close()
