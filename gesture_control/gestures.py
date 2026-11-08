"""손 목록 → 명령. 웹캠 없이 가짜 좌표로 시험할 수 있도록 MediaPipe 를 쓰지 않는다.

    재생/정지  한 손 OK 사인
    10초 이동  손등이 보이게 총 모양 (왼손 앞으로, 오른손 뒤로)
    볼륨       손바닥이 보이게 검지 위 / 엄지 아래
"""
import math

from . import config
from .common import Command

WRIST = 0
THUMB_TIP = 4
INDEX_KNUCKLE = 5
INDEX_JOINT, INDEX_TIP = 6, 8
MIDDLE_KNUCKLE = 9
PINKY_KNUCKLE = 17
OTHER_FINGERS = [(12, 10), (16, 14), (20, 18)]  # (손끝, 관절) 중지·약지·새끼


def hand_size(points):
    """손목~중지 뿌리 거리(픽셀). 카메라와의 거리가 달라도 비율로 비교할 수 있게 해 준다."""
    return math.dist(points[WRIST], points[MIDDLE_KNUCKLE])


def hand_side(hand):
    """카메라에 보이는 면. 손목→검지 뿌리, 손목→새끼 뿌리의 외적 부호로 판단한다."""
    wx, wy = hand.landmarks[WRIST]
    ix, iy = hand.landmarks[INDEX_KNUCKLE]
    px, py = hand.landmarks[PINKY_KNUCKLE]
    cross = (ix - wx) * (py - wy) - (iy - wy) * (px - wx)
    is_palm = cross > 0 if hand.label == "Right" else cross < 0
    return "palm" if is_palm else "back"


def is_victory(hands):
    """시작/종료 동작: 손이 하나만 보이고 브이 모양."""
    return len(hands) == 1 and hands[0].gesture == "Victory"


def is_finger_open(points, tip, joint):
    """손끝이 관절보다 손목에서 멀면 펴진 것."""
    wrist = points[WRIST]
    return math.dist(points[tip], wrist) > math.dist(points[joint], wrist)


def is_gun(points):
    """엄지·검지를 펴고 나머지 세 손가락을 접은 모양. 기본 제스처에 없어서 좌표로 판단한다."""
    thumb_open = math.dist(points[THUMB_TIP], points[INDEX_KNUCKLE]) > hand_size(points) * config.GUN_THUMB_RATIO
    index_open = is_finger_open(points, INDEX_TIP, INDEX_JOINT)
    others_folded = not any(is_finger_open(points, tip, joint) for tip, joint in OTHER_FINGERS)
    return thumb_open and index_open and others_folded


def is_ok(points):
    """엄지·검지 끝을 붙이고 나머지 세 손가락을 편 모양. 기본 제스처에 없어서 좌표로 판단한다."""
    touching = math.dist(points[THUMB_TIP], points[INDEX_TIP]) < hand_size(points) * config.OK_RATIO
    others_open = all(is_finger_open(points, tip, joint) for tip, joint in OTHER_FINGERS)
    return touching and others_open


def seek_command(hand):
    if hand_side(hand) != "back" or not is_gun(hand.landmarks):
        return None
    return Command.SEEK_FORWARD_10 if hand.label == "Left" else Command.SEEK_BACK_10


def volume_command(hand):
    if hand.gesture not in config.VOLUME_POSES:
        return None
    command, side = config.VOLUME_POSES[hand.gesture]
    if config.CHECK_HAND_SIDE and hand_side(hand) != side:
        return None
    return command


class OnceGate:
    """한 번 보낸 자세는 그 자세가 RELEASE_SEC 동안 안 보여야 다시 보낼 수 있다.

    손 이름·면과 상관없이 자세가 사라졌는지로만 풀기 때문에,
    라벨이 흔들리거나 인식이 잠깐 끊겨도 같은 자세로 다시 나가지 않는다.
    """

    def __init__(self):
        self.locked = False
        self.seen = 0.0

    def update(self, present, now):
        if present:
            self.seen = now
        elif now - self.seen >= config.RELEASE_SEC:
            self.locked = False


class CommandReader:
    def __init__(self):
        self.ok_gate = OnceGate()
        self.gun_gate = OnceGate()

    def update(self, hands, now):
        self.ok_gate.update(any(is_ok(hand.landmarks) for hand in hands), now)
        self.gun_gate.update(any(is_gun(hand.landmarks) for hand in hands), now)

        if len(hands) != 1:  # 양손이 보이면 손을 올리고 내리는 중일 수 있어 명령으로 보지 않는다
            return None

        hand = hands[0]
        if is_ok(hand.landmarks):
            return None if self.ok_gate.locked else Command.PLAY_PAUSE
        seek = seek_command(hand)
        if seek:
            return None if self.gun_gate.locked else seek
        return volume_command(hand)

    def lock(self, command):
        """명령을 보낸 뒤 호출한다. 자세를 풀 때까지 같은 명령이 다시 나가지 않게 한다."""
        if command == Command.PLAY_PAUSE:
            self.ok_gate.locked = True
        elif command in (Command.SEEK_FORWARD_10, Command.SEEK_BACK_10):
            self.gun_gate.locked = True
