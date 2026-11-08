"""여러 모듈이 함께 쓰는 데이터 형식 (조하연 구조).

    tracker.py ──list[Hand]──▶ gestures.py ──Command──▶ controller.py
"""
from dataclasses import dataclass
from enum import Enum


@dataclass
class Hand:
    """한 손의 인식 결과.

    label:     사용자의 실제 손 "Left" / "Right"
    gesture:   MediaPipe 기본 제스처 이름 (Open_Palm, Closed_Fist, Pointing_Up, Thumb_Down ...)
    score:     제스처 점수 (0~1)
    landmarks: 관절 21개의 (x, y). 거울 화면 기준 픽셀이라 사용자 오른쪽 = x 증가
    """

    label: str
    gesture: str
    score: float
    landmarks: list[tuple[float, float]]


class Command(Enum):
    PLAY_PAUSE = "PLAY/PAUSE"
    VOLUME_UP = "VOLUME UP"
    VOLUME_DOWN = "VOLUME DOWN"
    SEEK_BACK_10 = "BACK 10s"
    SEEK_FORWARD_10 = "FORWARD 10s"


COMMAND_KO = {
    Command.PLAY_PAUSE: "재생/일시정지",
    Command.VOLUME_UP: "볼륨 증가",
    Command.VOLUME_DOWN: "볼륨 감소",
    Command.SEEK_BACK_10: "10초 뒤로",
    Command.SEEK_FORWARD_10: "10초 앞으로",
}
