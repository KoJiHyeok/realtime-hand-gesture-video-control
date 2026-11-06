"""MediaPipe GestureRecognizer 를 감싼다. 프레임을 넣으면 손 목록이 나온다."""
from collections import namedtuple

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

import config

Hand = namedtuple("Hand", "side gesture score landmarks")


class Recognizer:
    def __init__(self):
        options = vision.GestureRecognizerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=config.MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=config.MIN_CONFIDENCE,
            min_tracking_confidence=config.MIN_CONFIDENCE,
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def recognize(self, rgb_frame, timestamp_ms):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        # VIDEO 모드는 프레임 순서를 알아야 해서 시각(timestamp_ms)을 함께 넘긴다
        result = self.recognizer.recognize_for_video(image, timestamp_ms)

        hands = []
        for i, landmarks in enumerate(result.hand_landmarks):
            best = result.gestures[i][0]
            gesture = best.category_name if best.score >= config.MIN_SCORE else "None"
            side = result.handedness[i][0].category_name
            hands.append(Hand(side, gesture, best.score, landmarks))
        return hands

    def close(self):
        self.recognizer.close()
