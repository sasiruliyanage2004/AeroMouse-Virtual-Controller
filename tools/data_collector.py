import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import csv
import os

# Create dataset directory
DATASET_DIR = "dataset"
if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)

CSV_FILE = os.path.join(DATASET_DIR, "gesture_data.csv")

# Create CSV and write headers if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        header = ['label']
        for i in range(21):
            header.extend([f'x_{i}', f'y_{i}', f'z_{i}'])
        writer.writerow(header)

# Initialize MediaPipe HandLandmarker
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core', 'hand_landmarker.task'))
if not os.path.exists(model_path):
    model_path = os.path.abspath('core/hand_landmarker.task')

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
current_label = 0
is_recording = False

print("\n" + "="*40)
print("🤖 JARVIS Custom Gesture Data Collector")
print("="*40)
print("INSTRUCTIONS:")
print("1. Press keys '0' to '9' to select gestures 0-9.")
print("2. Press 'A' for Gesture 10 (Zoom In).")
print("3. Press 'B' for Gesture 11 (Zoom Out).")
print("4. Press 'R' to start/stop recording frames.")
print("5. Press 'Q' to quit when finished.")
print("="*40 + "\n")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1) # Mirror image
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    detection_result = detector.detect(mp_image)
    
    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            h, w, c = frame.shape
            
            # Draw landmarks on the screen for feedback
            for lm in hand_landmarks:
                x, y = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (x, y), 5, (0, 255, 255), -1)
                
            if is_recording:
                # NORMALIZE the data relative to the wrist (Index 0).
                wrist_x = hand_landmarks[0].x
                wrist_y = hand_landmarks[0].y
                wrist_z = hand_landmarks[0].z
                
                row = [current_label]
                for lm in hand_landmarks:
                    row.extend([lm.x - wrist_x, lm.y - wrist_y, lm.z - wrist_z])
                
                with open(CSV_FILE, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
                    
    # UI Text Overlays
    status = "RECORDING (Move hand slightly)" if is_recording else "PAUSED"
    color = (0, 0, 255) if is_recording else (0, 255, 0)
    cv2.putText(frame, f"Label: {current_label} | Status: {status}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
    cv2.imshow("JARVIS Data Collector", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        is_recording = not is_recording
    elif ord('0') <= key <= ord('9'):
        current_label = int(chr(key))
    elif key == ord('a'):
        current_label = 10
    elif key == ord('b'):
        current_label = 11
        
cap.release()
detector.close()
cv2.destroyAllWindows()
