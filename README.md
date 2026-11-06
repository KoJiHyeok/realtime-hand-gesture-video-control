# 실시간 손 제스처 인식 기반 동영상 제어 시스템

Real-Time Hand Gesture Recognition-Based Video Control System

웹캠으로 손 제스처를 인식해 유튜브를 조작합니다.

## 설치 (Windows)
```
git clone https://github.com/KoJiHyeok/realtime-hand-gesture-video-control.git
cd realtime-hand-gesture-video-control
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
mkdir models
curl.exe -o models\gesture_recognizer.task https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
```

## 실행
```
.venv\Scripts\python main.py --test   # 키 없이 인식만 확인
.venv\Scripts\python main.py          # 실제 조작
```
실제 조작은 유튜브 영상을 클릭해 둔 뒤 영문 입력 상태에서 합니다. 종료는 터미널에서 Ctrl+C.

## 제스처
| 동작 | 결과 |
|---|---|
| 양손 손바닥 1초 | 시작 |
| 양손 주먹 1초 | 종료 |
| 한 손 OK | 재생/정지 |
| 한 손 오른쪽 쓸기 | +10초 |
| 한 손 왼쪽 쓸기 | -10초 |

값 조절은 `config.py`, 코드 설명은 `study.html`을 보세요.
