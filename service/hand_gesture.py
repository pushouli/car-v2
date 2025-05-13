import math
import time
from typing import Callable
import numpy as np
import cv2
import mediapipe as mp

from .hand_base import HandBase

# 初始化 MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def is_thumb_open(landmarks) -> bool:
    def vec(p1, p2):
        return np.array([p2.x - p1.x, p2.y - p1.y, p2.z - p1.z])

    cmc = landmarks[mp_hands.HandLandmark.THUMB_CMC]
    mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]
    tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    v1 = vec(cmc, mcp)
    v2 = vec(mcp, tip)

    # 防止除以0
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return True
    # print(f"v1: {v1}, v2: {v2}")  # 调试信息
    angle = math.degrees(
        math.acos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    )
    # print(f"Thumb angle: {angle:.2f} degrees")  # 调试信息
    return angle < 30  # 可调阈值


# 判断每根手指是否伸直
def get_fingers(hand_landmarks):
    finger_tips_ids = [
        mp_hands.HandLandmark.THUMB_TIP,
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP,
    ]

    finger_pip_ids = [
        mp_hands.HandLandmark.THUMB_IP,  # 虽然拇指不用了，保留结构一致
        mp_hands.HandLandmark.INDEX_FINGER_PIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        mp_hands.HandLandmark.RING_FINGER_PIP,
        mp_hands.HandLandmark.PINKY_PIP,
    ]

    fingers = [0] * 5  # 初始化五根手指的状态

    # 拇指使用角度判断
    # fingers.append(0 if is_thumb_open(hand_landmarks.landmark) else 1)
    if is_thumb_open(hand_landmarks.landmark):
        fingers[0] = 1

    for i in range(1, 5):
        tip_id = finger_tips_ids[i]
        pip_id = finger_pip_ids[i]
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[pip_id].y:
            fingers[i] = 1

    return fingers


class HandGesture(HandBase[list[int]]):
    def __init__(self):
        super().__init__()
        self.WINDOW_NAME = "HAND_GESTURE" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def process(self, hand_landmarks, hand_info, frame):
        # 左右手信息
        hand_label = hand_info.classification[0].label  # 'Left' or 'Right'

        # 统计手指
        fingers = get_fingers(hand_landmarks)

        # 画到屏幕上
        cv2.putText(
            frame,
            f"{hand_label} Hand: {fingers} fingers",
            (10, 50 if hand_label == "Right" else 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        return fingers

    def start(self, callback: Callable[[list[int]], None]):
        #处理回调函数的参数为None时，转换为空列表
        def wrapped_callback(fingers):
            if fingers is None:
                fingers = []
            callback(fingers)
        super().start(wrapped_callback)


if __name__ == "__main__":

    hand_gesture = HandGesture()
    def print_fingers(fingers: list[int]) -> None:
        print(f"Detected fingers: {fingers}")
    
    hand_gesture.start(print_fingers)
    time.sleep(5)
    hand_gesture.stop()
    time.sleep(5)
    print("Restarting...")
    hand_gesture.start(print_fingers)
    hand_gesture.wait()
