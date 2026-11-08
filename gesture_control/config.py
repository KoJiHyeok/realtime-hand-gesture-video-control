"""설정값 모음. 동작을 조절할 때는 이 파일만 고치면 된다."""
from pathlib import Path

from .common import Command

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "gesture_recognizer.task"
CAMERA_INDEX = 0

MIN_CONFIDENCE = 0.5     # 손 검출·추적 최소 신뢰도
MIN_SCORE = 0.5          # 제스처 점수가 이보다 낮으면 "None" 으로 취급

# 공통
STABLE_FRAMES = 3        # 자세가 이만큼 연속으로 보여야 인정
COOLDOWN_SEC = 0.7       # 재생/정지·10초 이동을 보낸 뒤 쉬는 시간
RELEASE_SEC = 0.3        # 자세가 이만큼 안 보여야 풀린 것으로 보고 다시 보낼 수 있다

# 시작/종료 (한 손 브이)
HOLD_SEC = 1.0           # 브이를 이만큼 유지하면 시작/종료가 바뀐다
NO_HAND_SEC = 5.0        # 인식 중 손이 이만큼 안 보이면 대기로 돌아간다

# 재생/정지 (한 손 OK)
OK_RATIO = 0.3           # 엄지 끝~검지 끝 거리 < 손 크기 x 이 값 → 붙인 것

# 10초 이동 (손등이 보이게 총 모양: 왼손 앞으로, 오른손 뒤로)
GUN_THUMB_RATIO = 0.5    # 엄지 끝~검지 뿌리 거리 > 손 크기 x 이 값 → 엄지가 펴진 것

# 볼륨: {제스처: (명령, 보여야 하는 손의 면)}. "palm" 손바닥, "back" 손등
VOLUME_POSES = {
    "Pointing_Up": (Command.VOLUME_UP, "palm"),
    "Thumb_Down": (Command.VOLUME_DOWN, "palm"),
}
CHECK_HAND_SIDE = True   # False 면 볼륨에서 손바닥/손등을 따지지 않는다
VOLUME_REPEAT_SEC = 0.5  # 자세를 유지하면 이 간격으로 볼륨을 계속 바꾼다

# 터미널에 찍히는 이름
NAMES = {
    "Left": "왼손", "Right": "오른손", "palm": "손바닥", "back": "손등",
    "Open_Palm": "손 펴짐", "Closed_Fist": "주먹", "Pointing_Up": "검지 위",
    "Thumb_Up": "엄지 위", "Thumb_Down": "엄지 아래", "Victory": "브이",
    "ILoveYou": "아이러브유", "None": "제스처 아님", "OK": "OK", "Gun": "총 모양",
}
