"""메인 루프: 프레임 읽기 → 인식 → 상태 → 명령 → 필터 → 키 입력. 종료는 Ctrl+C.

python main.py         실제 키 입력
python main.py --test  키 없이 제스처 인식만 확인
"""
import sys
import time

import cv2

import config
import controller
import gestures
from check import Checklist
from recognizer import Recognizer
from state import RemoteState


def status_line(mode, hands):
    parts = [f"{config.NAMES[hand.side]}: {config.NAMES[hand.gesture]}" for hand in hands]
    return f"[{config.NAMES[mode]}] " + (" / ".join(parts) if parts else "손 없음")


def main():
    camera = cv2.VideoCapture(config.CAMERA_INDEX)  # OpenCV 는 프레임 읽기에만 쓴다
    if not camera.isOpened():
        raise SystemExit("카메라를 열 수 없습니다.")

    recognizer = Recognizer()
    swipe = gestures.SwipeDetector()
    state = RemoteState()
    last_line = None
    checklist = Checklist() if "--test" in sys.argv else None
    print("시작: 양손 손바닥 1초 / 종료: 양손 주먹 1초 / 프로그램 끝내기: Ctrl+C")

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                continue

            # BGR → RGB. 좌우 반전은 하지 않는다 (반전하면 왼손/오른손 라벨이 뒤바뀐다)
            rgb = frame[:, :, ::-1].copy()
            now = time.monotonic()
            hands = recognizer.recognize(rgb, int(now * 1000))

            before = state.mode
            state.update_mode(now, hands)
            if checklist and state.mode != before:
                if state.mode == "ACTIVE":
                    checklist.mark("시작")
                elif gestures.both_hands(hands, "Closed_Fist"):  # 손 없음 5초로 꺼진 건 제외
                    checklist.mark("종료")

            line = status_line(state.mode, hands)
            if line != last_line:
                print(line)
                last_line = line

            if state.mode == "ACTIVE":
                command = gestures.get_command(hands, swipe, now)
                if state.should_fire(command, now):
                    key = config.KEYS[command]
                    name = config.NAMES[command]
                    print(f"[{config.NAMES['ACTIVE']}] {name} -> {key} 키")
                    if checklist:
                        checklist.mark(name)
                    else:
                        controller.press(key)
            else:
                swipe.reset()
    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        recognizer.close()


if __name__ == "__main__":
    main()
