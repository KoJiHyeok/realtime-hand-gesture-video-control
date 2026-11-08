"""MediaPipe 제스처 모델을 models/ 폴더에 내려받는다. 이미 있으면 받지 않는다."""
from pathlib import Path
import urllib.request

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task"
)
MODEL_PATH = Path(__file__).resolve().parent / "models" / "gesture_recognizer.task"

if MODEL_PATH.exists():
    print(f"이미 있습니다: {MODEL_PATH}")
else:
    MODEL_PATH.parent.mkdir(exist_ok=True)
    print(f"내려받는 중: {MODEL_URL}")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print(f"완료: {MODEL_PATH}")
