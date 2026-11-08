"""MediaPipe GestureRecognizer 로 프레임에서 손과 제스처를 찾는다."""
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

from . import config
from .common import Hand


class HandTracker:
    def __init__(self):
        options = vision.GestureRecognizerOptions(
            # 경로에 한글이 있어도 열리도록 파일 내용을 직접 넘긴다
            base_options=BaseOptions(model_asset_buffer=config.MODEL_PATH.read_bytes()),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=config.MIN_CONFIDENCE,
            min_tracking_confidence=config.MIN_CONFIDENCE,
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def detect(self, frame_bgr, timestamp_ms):
        """카메라 원본(BGR)을 받는다. 반전한 영상을 넣으면 왼손/오른손이 뒤바뀐다."""
        height, width = frame_bgr.shape[:2]
        rgb = frame_bgr[:, :, ::-1].copy()
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.recognizer.recognize_for_video(image, timestamp_ms)

        hands = []
        for i, landmarks in enumerate(result.hand_landmarks):
            best = result.gestures[i][0]
            gesture = best.category_name if best.score >= config.MIN_SCORE else "None"
            # 좌표만 거울 화면 기준으로 뒤집는다 (사용자 오른쪽 = x 증가)
            points = [((1.0 - p.x) * width, p.y * height) for p in landmarks]
            hands.append(Hand(result.handedness[i][0].category_name, gesture, best.score, points))
        return hands

    def close(self):
        self.recognizer.close()
