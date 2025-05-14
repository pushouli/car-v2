import cv2
from picamera2 import Picamera2
class Camera:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (1920, 1080)}
        )
        self.picam2.configure(config)
        self.picam2.start()
        print("Preview size:", self.picam2.stream_configuration("main")["size"])

    def capture_frame(self):
        frame = self.picam2.capture_array()
        frame = cv2.flip(frame, 1)
        return frame

    def stop(self):
        if self.picam2 is None:
            print("Camera not started.")
            return
        self.picam2.stop()
        self.picam2.close()
        self.picam2 = None
        print("Camera stopped.")
