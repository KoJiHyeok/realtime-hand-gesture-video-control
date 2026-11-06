"""설정값 모음."""
import os

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "models", "gesture_recognizer.task")
CAMERA_INDEX = 0

MIN_CONFIDENCE = 0.5   # 손 검출·추적 최소 신뢰도
MIN_SCORE = 0.5        # 제스처 점수가 이보다 낮으면 "None" 으로 취급

HOLD_SEC = 1.0         # 양손 동작을 이만큼 유지해야 상태가 바뀐다
NO_HAND_SEC = 5.0      # ACTIVE 에서 손이 이만큼 안 보이면 IDLE 로

STABLE_FRAMES = 3      # 같은 명령이 이만큼 연속으로 나와야 인정
COOLDOWN_SEC = 1.0     # 키를 보낸 뒤 쉬는 시간

OK_RATIO = 0.3          # 엄지-검지 끝 거리 < 손 크기 x 이 값 → OK
SWIPE_WINDOW_SEC = 0.8  # 이 시간 동안의 이동량을 본다
SWIPE_RATIO = 1.0       # x 이동량 > 손 크기 x 이 값 → 쓸기

# 명령 → 유튜브 단축키
KEYS = {
    "OK": "k",           # 재생/정지
    "SWIPE_RIGHT": "l",  # +10초
    "SWIPE_LEFT": "j",   # -10초
}

# 터미널에 찍히는 이름
NAMES = {
    "IDLE": "대기", "ACTIVE": "인식 중",
    "Left": "왼손", "Right": "오른손",
    "Open_Palm": "손바닥", "Closed_Fist": "주먹", "Pointing_Up": "검지 위",
    "Thumb_Up": "엄지 위", "Thumb_Down": "엄지 아래", "Victory": "브이",
    "ILoveYou": "아이러브유", "None": "제스처 아님",
    "OK": "OK (재생/정지)", "SWIPE_RIGHT": "오른쪽 쓸기 (+10초)", "SWIPE_LEFT": "왼쪽 쓸기 (-10초)",
}
