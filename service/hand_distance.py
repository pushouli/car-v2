import math
from typing import Callable
import cv2
import mediapipe as mp

from .hand_base import HandBase

# 初始化 MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def calculate_normalized_distance(point1, point2):
    """计算两个关键点之间归一化后的欧氏距离"""
    return math.hypot(point2.x - point1.x, point2.y - point1.y)


def calculate_relative_distance(point1, point2, reference_point1, reference_point2):
    """计算两个关键点之间的相对距离，基于参考点的距离"""
    distance = calculate_normalized_distance(point1, point2)
    reference_distance = calculate_normalized_distance(
        reference_point1, reference_point2
    )
    if reference_distance == 0:  # 避免除以零
        return 0
    return distance / reference_distance


def map_distance_to_percent(relative_distance, min_ratio=0.2, max_ratio=1.5):
    """把相对距离映射到亮度百分比"""
    relative_distance = max(
        min_ratio, min(max_ratio, relative_distance)
    )  # 限制在合理范围内
    percent = (relative_distance - min_ratio) / (max_ratio - min_ratio) * 100
    percent = int(percent)
    return percent


def get_distance(hand_landmarks, frame):
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    pinky_base = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]

    # 计算相对距离
    relative_distance = calculate_relative_distance(
        thumb_tip, index_tip, wrist, pinky_base
    )

    # 转成亮度百分比
    percent = map_distance_to_percent(relative_distance)
    h, w, _ = frame.shape
    thumb_pos = (int(thumb_tip.x * w), int(thumb_tip.y * h))
    index_pos = (int(index_tip.x * w), int(index_tip.y * h))
    # 控制台输出
    # print(f"相对距离: {relative_distance:.4f}, 亮度: {percent}%")
    return percent, thumb_pos, index_pos


class HandDistance(HandBase[float]):
    def __init__(self):
        super().__init__()
        self.WINDOW_NAME = "HAND_DISTANCE"
        self.last_percent = []

    def process(self, hand_landmarks, hand_info, frame):
        percent, thumb_pos, index_pos = get_distance(hand_landmarks, frame)
        # 画线
        cv2.line(frame, thumb_pos, index_pos, (255, 0, 255), 10)

        # 显示亮度
        mid_x = (thumb_pos[0] + index_pos[0]) // 2
        mid_y = (thumb_pos[1] + index_pos[1]) // 2
        cv2.putText(
            frame,
            f"{percent}%",
            (mid_x, mid_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            5,
            (0, 255, 0),
            5,
        )
        return percent

    def start(self, callback: Callable[[float], None]):
        # 处理回调函数的参数为None时，转换为0
        def wrapped_callback(percent):
            if percent is None:
                percent = 0
            callback(percent)

        super().start(wrapped_callback)


if __name__ == "__main__":

    def print_percent(percent):
        print(f"Detected percent: {percent}")

    hand_distance = HandDistance()
    hand_distance.start(print_percent)
    # time.sleep(100)
    hand_distance.wait()
