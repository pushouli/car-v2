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


def is_finger_open(landmarks, mcp_id, pip_id, tip_id):
    """
    判断一根手指是否伸直：通过 MCP→PIP 和 PIP→TIP 向量间的夹角判断
    """

    def vec(p1, p2):
        return np.array([p2.x - p1.x, p2.y - p1.y, p2.z - p1.z])

    v1 = vec(landmarks[mcp_id], landmarks[pip_id])
    v2 = vec(landmarks[pip_id], landmarks[tip_id])

    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return False

    angle = math.degrees(
        math.acos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    )

    return angle < 30  # 阈值可以调整


# 判断每根手指是否伸直
def get_fingers(hand_landmarks):
    fingers = [0] * 5

    # 拇指
    if is_thumb_open(hand_landmarks.landmark):
        fingers[0] = 1

    # 其它四指：用角度判断
    finger_mcp_ids = [
        mp_hands.HandLandmark.INDEX_FINGER_MCP,
        mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
        mp_hands.HandLandmark.RING_FINGER_MCP,
        mp_hands.HandLandmark.PINKY_MCP,
    ]
    finger_pip_ids = [
        mp_hands.HandLandmark.INDEX_FINGER_PIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        mp_hands.HandLandmark.RING_FINGER_PIP,
        mp_hands.HandLandmark.PINKY_PIP,
    ]
    finger_tip_ids = [
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP,
    ]

    for i in range(4):
        if is_finger_open(
            hand_landmarks.landmark,
            finger_mcp_ids[i],
            finger_pip_ids[i],
            finger_tip_ids[i],
        ):
            fingers[i + 1] = 1

    return fingers


class HandGesture(HandBase[list[int]]):
    def __init__(self):
        super().__init__()
        self.WINDOW_NAME = "HAND_GESTURE" + time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime()
        )

    def process(self, hand_landmarks, hand_info, frame):
        # 左右手信息
        hand_label = hand_info.classification[0].label  # 'Left' or 'Right'

        # 统计手指
        fingers = get_fingers(hand_landmarks)

        # 画到屏幕上
        cv2.putText(
            frame,
            f"{hand_label} Hand: {fingers} fingers",
            (10, 100 if hand_label == "Right" else 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            4,
            (0, 0, 0),
            5,
        )
        return fingers

    def start(self, callback: Callable[[list[int]], None]):
        # 处理回调函数的参数为None时，转换为空列表
        def wrapped_callback(fingers):
            if fingers is None:
                fingers = [0, 0, 0, 0, 0]
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
