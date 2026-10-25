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
            num_hands=2, 
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        self.prev_y = None
        self.is_sleeping = True
        self.locked_handedness = None 
        
    def process_frame(self, frame):
        action = None
        
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self.detector.detect(mp_image)
        except Exception as e:
            return frame, None

        if detection_result.hand_landmarks:
            for idx in range(len(detection_result.hand_landmarks)):
                hand_landmarks = detection_result.hand_landmarks[idx]
                handedness = detection_result.handedness[idx][0].category_name
                
                # HAND LOCKING LOGIC
                if not self.is_sleeping and self.locked_handedness is not None:
                    if handedness != self.locked_handedness:
                        continue 
                
                # BOUNDARY ANTI-GLITCH CHECK
                is_inside_frame = True
                for lm in hand_landmarks:
                    if lm.x < 0.0 or lm.x > 1.0 or lm.y < 0.0 or lm.y > 1.0:
                        is_inside_frame = False
                        break
                if not is_inside_frame:
                    continue 
                        
                h, w, c = frame.shape
                
                # REVERTED TO SIMPLE ROBUST FINGER DETECTION
                is_index_up = hand_landmarks[8].y < hand_landmarks[6].y
                is_middle_up = hand_landmarks[12].y < hand_landmarks[10].y
                is_ring_up = hand_landmarks[16].y < hand_landmarks[14].y
                is_pinky_up = hand_landmarks[20].y < hand_landmarks[18].y
                
                is_index_down = not is_index_up
                is_middle_down = not is_middle_up
                is_ring_down = not is_ring_up
                is_pinky_down = not is_pinky_up
                
                # Thumbs Up (Wake/Sleep): Thumb is high, all other fingers strictly folded
                is_thumb_up_only = (hand_landmarks[4].y < hand_landmarks[5].y) and is_index_down and is_middle_down and is_ring_down and is_pinky_down
                
                is_fist = is_index_down and is_middle_down and is_ring_down and is_pinky_down and not is_thumb_up_only
                is_open_hand = is_index_up and is_middle_up and is_ring_up and is_pinky_up
                
                index_x = hand_landmarks[8].x
                index_y = hand_landmarks[8].y
                
                pinch_dist = math.hypot(hand_landmarks[8].x - hand_landmarks[4].x, 
                                        hand_landmarks[8].y - hand_landmarks[4].y)
                
                # Visual pinch feedback
                if not self.is_sleeping and pinch_dist < 0.08:
                    x1, y1 = int(hand_landmarks[8].x * w), int(hand_landmarks[8].y * h)
                    x2, y2 = int(hand_landmarks[4].x * w), int(hand_landmarks[4].y * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

                # Prioritize Wake/Sleep Toggle
                if is_thumb_up_only:
                    action = ('toggle_state', handedness) 
                    break 
                
                # Process Actions ONLY if Active
                if not self.is_sleeping:
                    # Priority 1: Pinch (Click)
                    if pinch_dist < 0.08:
                        action = ('click', None)
                        self.prev_y = None
                        
                    # Priority 2: Move (Strictly ONLY index finger up)
                    elif is_index_up and is_middle_down and is_ring_down and is_pinky_down:
                        self.prev_y = None
                        action = ('move', (index_x, index_y))
                        
                    # Priority 3: Scroll (Strictly ONLY index + middle up)
                    elif is_index_up and is_middle_up and is_ring_down and is_pinky_down:
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
                            
                    # Priority 4: Maximize (All fingers up)
                    elif is_open_hand:
                        action = ('maximize_window', None)
                        
                    # Priority 5: Minimize (All fingers down)
                    elif is_fist:
                        action = ('minimize_window', None)
                        
                    else:
                        self.prev_y = None 
                    
                    if action:
                        break # Action processed for locked hand
        else:
            self.prev_y = None

        return frame, action

    def release(self):
        try:
            self.detector.close()
        except Exception:
            pass
