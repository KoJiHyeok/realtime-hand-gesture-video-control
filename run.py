"""실시간 손 제스처 인식 기반 동영상 제어 시스템.

python run.py         유튜브를 실제로 제어
python run.py --test  키 없이 제스처 인식만 확인

끝내기: 웹캠 창에서 q 또는 ESC, 터미널에서 Ctrl+C
"""
import sys
import time

import cv2

from gesture_control import config
from gesture_control.check import Checklist
from gesture_control.common import COMMAND_KO
from gesture_control.gestures import CommandReader, hand_side, is_gun, is_ok, is_victory
from gesture_control.state import RemoteState
from gesture_control.tracker import HandTracker

WINDOW = "Gesture Control"
BONES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11),
         (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def pose_name(hand):
    """좌표로 판별하는 자세를 먼저 보고, 아니면 MediaPipe 제스처 이름을 쓴다."""
    if is_ok(hand.landmarks):
        return "OK"
    if is_gun(hand.landmarks):
        return "Gun"
    return hand.gesture


def status_line(active, hands):
    mode = "인식 중" if active else "대기"
    parts = [f"{config.NAMES[h.label]}: {config.NAMES.get(pose_name(h), pose_name(h))}"
             f"({config.NAMES[hand_side(h)]})" for h in hands]
    return f"[{mode}] " + (" / ".join(parts) if parts else "손 없음")


def put_text(frame, text, y, color):
    cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)


def draw(frame, active, hands, last_command):
    """미리보기 창. OpenCV 는 한글을 못 그려서 화면 글자는 영어로 쓴다."""
    view = cv2.flip(frame, 1)
    for hand in hands:
        points = [(int(x), int(y)) for x, y in hand.landmarks]
        for a, b in BONES:
            cv2.line(view, points[a], points[b], (255, 255, 255), 2)
        for point in points:
            cv2.circle(view, point, 3, (0, 200, 0), -1)
        put_text(view, f"{hand.label} {pose_name(hand)} {hand_side(hand)}", min(points[0][1] + 25, view.shape[0] - 10), (0, 220, 255))
    put_text(view, "ACTIVE" if active else "IDLE - V sign 1s", 25, (0, 200, 0) if active else (0, 220, 255))
    if last_command:
        put_text(view, last_command.value, 50, (0, 200, 0))
    cv2.imshow(WINDOW, view)


def start_control():
    """유튜브 제어 스레드를 시작하고, 제어할 창을 고를 때까지 기다린다."""
    from gesture_control.worker import ControlWorker

    worker = ControlWorker()
    worker.start()
    worker.ready.wait()
    return worker


def main():
    if not config.MODEL_PATH.exists():
        raise SystemExit("모델 파일이 없습니다. 먼저 실행하세요: python download_model.py")

    checklist = Checklist() if "--test" in sys.argv else None
    worker = None if checklist else start_control()

    camera = cv2.VideoCapture(config.CAMERA_INDEX)  # OpenCV 는 웹캠과 미리보기 창에만 쓴다
    if not camera.isOpened():
        raise SystemExit("카메라를 열 수 없습니다.")
    tracker = HandTracker()
    reader = CommandReader()
    state = RemoteState()
    last_line = None
    last_command = None
    last_ms = 0
    print("시작/종료: 한 손 브이 1초 / 끝내기: 웹캠 창에서 q")

    cv2.namedWindow(WINDOW)
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_TOPMOST, 1)  # 유튜브를 보면서 상태를 확인하도록 항상 위에
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                continue

            now = time.monotonic()
            last_ms = max(int(now * 1000), last_ms + 1)  # VIDEO 모드는 시각이 계속 증가해야 한다
            hands = tracker.detect(frame, last_ms)

            was_active = state.active
            state.update_mode(now, hands)
            if state.active != was_active:
                print("=== 인식 시작 ===" if state.active else "=== 인식 종료 ===", flush=True)
                if checklist:
                    if state.active:
                        checklist.mark("시작")
                    elif is_victory(hands):  # 손 없음으로 꺼진 건 제외
                        checklist.mark("종료")

            line = status_line(state.active, hands)
            if line != last_line:
                print(line, flush=True)
                last_line = line

            if state.active:
                command = state.next_command(reader, hands, now)
                if command:
                    last_command = command
                    print(f">>> {COMMAND_KO[command]}", flush=True)
                    if checklist:
                        checklist.mark(COMMAND_KO[command])
                    else:
                        worker.submit(command)

            draw(frame, state.active, hands, last_command)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
