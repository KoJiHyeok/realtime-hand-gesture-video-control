"""인식 결과 → 명령 이름. OK 와 쓸기는 기본 제스처에 없어서 랜드마크로 직접 계산한다."""
import math
from collections import deque

import config

WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_KNUCKLE = 9
OTHER_FINGERS = [(12, 10), (16, 14), (20, 18)]  # (손끝, 관절) 중지·약지·새끼


def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def hand_size(landmarks):
    """손목~중지 뿌리 거리. 카메라와의 거리가 달라져도 비율로 비교할 수 있게 해 준다."""
    return distance(landmarks[WRIST], landmarks[MIDDLE_KNUCKLE])


def is_finger_open(landmarks, tip, joint):
    """손끝이 관절보다 손목에서 멀면 펴진 것."""
    wrist = landmarks[WRIST]
    return distance(landmarks[tip], wrist) > distance(landmarks[joint], wrist)


def is_ok(landmarks):
    touching = (distance(landmarks[THUMB_TIP], landmarks[INDEX_TIP])
                < hand_size(landmarks) * config.OK_RATIO)
    others_open = all(is_finger_open(landmarks, tip, joint) for tip, joint in OTHER_FINGERS)
    return touching and others_open


def both_hands(hands, gesture):
    return len(hands) == 2 and all(hand.gesture == gesture for hand in hands)


class SwipeDetector:
    def __init__(self):
        self.history = deque()  # (시각, 손목 x, 손목 y)

    def reset(self):
        self.history.clear()

    def update(self, now, landmarks):
        x, y = landmarks[WRIST].x, landmarks[WRIST].y
        self.history.append((now, x, y))
        while now - self.history[0][0] > config.SWIPE_WINDOW_SEC:
            self.history.popleft()

        moved = x - self.history[0][1]
        moved_y = y - self.history[0][2]
        if abs(moved) < hand_size(landmarks) * config.SWIPE_RATIO:
            return None
        if abs(moved) < abs(moved_y):  # 옆보다 위아래로 더 움직였으면 손을 내리는 동작이다
            return None
        # 카메라는 나를 마주 보므로, 내가 오른쪽으로 움직이면 영상의 x 는 작아진다
        return "SWIPE_RIGHT" if moved < 0 else "SWIPE_LEFT"


def get_command(hands, swipe, now):
    if not hands:  # 빠르게 움직이면 손을 잠깐 놓친다 → 쓸기 기록은 지우지 않는다
        return None
    if len(hands) == 2:  # 양손이 보이면 명령으로 보지 않는다 (시작/종료 동작과 구분)
        swipe.reset()
        return None

    hand = hands[0]
    if is_ok(hand.landmarks):
        return "OK"
    return swipe.update(now, hand.landmarks)
