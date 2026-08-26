import cv2

class CameraManager:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

    def start(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        return self.cap.isOpened()

    def get_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Flip the frame horizontally for a later selfie-view display
                frame = cv2.flip(frame, 1)
                return True, frame
        return False, None

    def stop(self):
        if self.cap:
            self.cap.release()
