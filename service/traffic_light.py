import time
from typing import Callable
from .base.camera import Camera
from ultralytics import YOLO

from .base.video import show_frame


class TrafficLight:
    def __init__(self):
        self.camera: Camera = None
        self.model: YOLO = None
        self.running = False
        self.thread = None
        self.last_value: str = None
        self.callback = None


    def run(self):
        self.model = YOLO("models/lights.pt")
        self.camera = Camera()
        while self.running:
            frame = self.camera.capture_frame()
            value: str = ""
            results = self.model(frame, verbose=False)  # 执行推理
            # 解析检测结果
            result = results[0]
            boxes = result.boxes  # 检测框对象
            for box in boxes:
                conf = box.conf.item()  # 置信度
                if conf <= 0.5:
                    continue
                cls_id = box.cls.item()  # 类别ID
                cls_name = self.model.names[cls_id]  # 类别名称
                if cls_name == "RedCircular":
                    value = "red"
                elif cls_name == "GreenCircular":
                    value = "green"
            # print("检测到物体数量:", len(list))
            image = results[0].plot()  # 获取渲染后的图像
            show_frame(image)
            if self.last_value != value:
                print("检测到的交通灯颜色:", value)
                # 触发外部回调
                self.callback(value)
                self.last_value = value
            # print("Processing frame" + str(frame.shape))
            time.sleep(0.1)

        show_frame(None)

    def start(self, callback: Callable[[str], None]):
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

        self.thread = None
        self.callback = None

        # # 停止摄像头
        camera = self.camera
        if camera:
            camera.stop()
            self.camera = None
        

        print("Camera stopped and windows closed.")

    def stop(self):
        self._stop(wait=True)
        print("TrafficLight stopped.")

if __name__ == "__main__":
    traffic_light = TrafficLight()
    traffic_light.start(lambda x: print("Callback:", x))
    time.sleep(50)
    traffic_light.stop()
    print("Main thread finished.")