import time
from typing import Callable, Generic, TypeVar
import cv2
from picamera2 import Picamera2
import mediapipe as mp
from .video import set_frame as set_video_frame

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

T = TypeVar("T")


class HandBase(Generic[T]):
    def __init__(self):
        self.picam2: Picamera2 = None
        self.hands = None
        self.running = False
        self.thread = None
        self.last_value: T = None
        self.callback = None
        # 设置绘图样式：绿色点，大圆，红线，粗线
        self.point_style = mp_drawing.DrawingSpec(
            color=(0, 0, 255), thickness=3, circle_radius=5
        )
        self.line_style = mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=8)

    def process(self, hand_landmarks, hand_info, frame) -> T:
        pass

    def run(self):

        self.WINDOW_NAME = "HAND" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print("Starting run..." + self.WINDOW_NAME)
        picam2 = Picamera2()
        self.picam2 = picam2
        WINDOW_NAME = self.WINDOW_NAME
        # 使用预设的处理好的配置
        config = picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (1024, 768)}
        )
        picam2.configure(config)
        picam2.start()
        print("Preview size:", picam2.stream_configuration("main")["size"])

        # 设置 Hands 参数
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self.hands = hands

        while self.running:
            frame = picam2.capture_array()
            frame = cv2.flip(frame, 1)
            results = hands.process(frame)
            value: T = None
            if results.multi_hand_landmarks:
                for hand_landmarks, hand_info in zip(
                    results.multi_hand_landmarks, results.multi_handedness
                ):
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        self.point_style,
                        self.line_style,
                    )

                    value = self.process(hand_landmarks, hand_info, frame)

            # 假设 frame 是高分辨率图像
            # small_frame = cv2.resize(frame, (480, 320), interpolation=cv2.INTER_LINEAR)
            set_video_frame(frame)
            if self.last_value != value:
                # 触发外部回调
                self.callback(value)
                self.last_value = value
            # print("Processing frame" + str(frame.shape))
            time.sleep(0.1)

        set_video_frame(None)

    def start(self, callback: Callable[[T], None]):
        # 使用线程
        import threading

        print("Starting camera...")
        self.callback = callback
        self.running = True
        thread = threading.Thread(target=self.run)
        self.thread = thread
        thread.start()
        # self.run()
        print("Camera started.")

    def wait(self):
        # 等待线程结束
        if self.thread is not None:
            self.thread.join()
            print("Thread joined.")
        else:
            print("Thread is None, cannot join.")

    def _stop(self, wait: bool = True):
        self.running = False

        if wait:
            self.wait()

        if self.hands:
            self.hands.close()
            self.hands = None
        # 停止摄像头
        picam2 = self.picam2
        if picam2:
            picam2.stop()
            picam2.close()
            self.picam2 = None

        self.thread = None
        self.callback = None

        print("Camera stopped and windows closed.")

    def stop(self):
        self._stop(wait=True)
        print("HandGesture stopped.")
