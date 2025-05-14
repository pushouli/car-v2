import time
from typing import Callable
from gpiozero import DistanceSensor


class FrontDistance:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_value: int = None
        self.callback = None
        self.sensor = None

    def run(self):
        self.sensor = DistanceSensor(echo=20, trigger=16)
        self.last_value = 0
        while self.running:
            value = self.sensor.distance * 100  # 单位：米，乘100为厘米
            value = int(value)
            if value >= 100:
                value = -1
            if self.last_value != value:
                # print("距离变化:", value)
                # 触发外部回调
                self.callback(value)
                print("FrontDistance change:", value)
                self.last_value = value
            time.sleep(0.1)

    def start(self, callback: Callable[[str], None]):
        # 使用线程
        import threading

        print("Starting FrontDistance...")
        self.callback = callback
        self.running = True
        thread = threading.Thread(target=self.run)
        self.thread = thread
        thread.start()
        # self.run()
        print("FrontDistance started.")

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
        sensor: DistanceSensor = self.sensor
        if sensor:
            sensor.close()
            self.sensor = None

        print("FrontDistance stopped and windows closed.")

    def stop(self):
        self._stop(wait=True)
        print("FrontDistance stopped.")


if __name__ == "__main__":
    front_distance = FrontDistance()
    front_distance.start(lambda x: print("Callback:", x))
    time.sleep(30)
    front_distance.stop()
