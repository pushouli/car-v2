import threading
import time
import cv2

frames = [None]
event = threading.Event()


def set_frame(frame):
    frames[0] = frame
    event.set()


# @app.route('/video')
# def video_feed():
#     return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def consumer():
    last = None
    while True:
        event.wait()
        event.clear()
        # print("Consumer thread started")
        try:
            frame = frames[0]
            if frame is None and last is not None:
                cv2.moveWindow("Frame", -1000, -1000)
            if frame is None:
                last = None
                continue
            cv2.imshow("Frame", frame)
            # print(frame)
            # prqint(last)
            if frame is not None and last is None:
                cv2.moveWindow("Frame", 10, 10)
            last = frame
            if cv2.waitKey(1) & 0xFF == ord("q"):
                exit()

        except Exception as e:
            print(f"Error processing frame: {e}")
            break
        time.sleep(0.1)


t2 = threading.Thread(target=consumer)
t2.start()
