# 실시간 손 제스처 인식 기반 동영상 제어 시스템

웹캠으로 손 제스처를 인식해 유튜브를 제어합니다. Windows 전용입니다.

## 설치

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_model.py
```

## 실행

유튜브 영상을 연 상태에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe run.py         # 유튜브 제어
.\.venv\Scripts\python.exe run.py --test  # 키 없이 인식만 확인
```

끝내기: 웹캠 창에서 `q` 또는 `ESC`

## 제스처

| 동작 | 기능 |
|---|---|
| 한 손 브이 1초 유지 | 인식 시작 / 종료 |
| 한 손 OK 사인 | 재생/일시정지 |
| 손등이 보이게 왼손 총 모양 | 10초 앞으로 |
| 손등이 보이게 오른손 총 모양 | 10초 뒤로 |
| 손바닥이 보이게 검지를 위로 | 볼륨 증가 (유지하면 반복) |
| 손바닥이 보이게 엄지를 아래로 | 볼륨 감소 (유지하면 반복) |

총 모양은 엄지와 검지를 펴고 나머지를 접은 자세입니다. 브이·OK·총 모양은 손을 풀어야 다시 인식합니다.
명령은 손이 하나만 보일 때 동작합니다. 값 조절은 `gesture_control/config.py`에서 합니다.
