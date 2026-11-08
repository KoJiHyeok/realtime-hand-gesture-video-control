"""웹캠 없이 가짜 손 좌표로 제스처 판별을 시험한다. 실행: python -m unittest discover -s tests -t ."""
import unittest

from gesture_control.common import Command, Hand
from gesture_control.gestures import CommandReader, hand_side, is_gun, is_ok
from gesture_control.state import RemoteState

FPS = 30


def make_hand(x=320.0, y=300.0, gesture="None", label="Right", palm=True, shape="fist"):
    """손목 (x, y), 손 크기 60px 인 세운 손. shape: fist(전부 접음), gun, ok."""
    index_x = -20 if (label == "Right") == palm else 20
    points = [(x, y)] * 21
    for i, (base_x, base_y) in {5: (index_x, -60), 9: (0, -60), 13: (-index_x / 2, -58), 17: (-index_x, -55)}.items():
        points[i] = (x + base_x, y + base_y)
        points[i + 1] = (x + base_x, y + base_y - 25)  # 가운데 관절
        points[i + 2] = (x + base_x, y + base_y - 35)
        finger_open = (shape == "gun" and i == 5) or (shape == "ok" and i != 5)
        # 편 손가락은 손끝이 더 멀고, 접은 손가락은 손끝이 손바닥 쪽으로 돌아온다
        points[i + 3] = (x + base_x, y + base_y - 45) if finger_open else (x + base_x, y + base_y + 10)
    points[4] = (x + index_x * 3, y - 30) if shape == "gun" else (x + index_x, y - 45)
    if shape == "ok":
        points[8] = (x + index_x, y - 50)
        points[4] = (x + index_x, y - 45)
    return Hand(label, gesture, 0.9, points)


def play(frames):
    """frames: 프레임별 손 목록. 실제로 나간 명령 목록을 돌려준다."""
    reader, state = CommandReader(), RemoteState()
    state.active = True
    fired = []
    for i, hands in enumerate(frames):
        now = 100 + i / FPS
        state.last_seen = now  # 이 시험에서는 손 없음으로 꺼지지 않게 한다
        command = state.next_command(reader, hands, now)
        if command:
            fired.append(command)
    return fired


def still(n, **kw):
    return [[make_hand(**kw)] for _ in range(n)]


def gun(n, label="Left", palm=False):
    return still(n, shape="gun", label=label, palm=palm)


def ok(n):
    return still(n, shape="ok")


class TestShapes(unittest.TestCase):
    def test_gun_is_detected(self):
        self.assertTrue(is_gun(make_hand(shape="gun").landmarks))

    def test_folded_thumb_is_not_gun(self):
        hand = make_hand(shape="gun")
        hand.landmarks[4] = hand.landmarks[5]
        self.assertFalse(is_gun(hand.landmarks))

    def test_open_middle_finger_is_not_gun(self):
        hand = make_hand(shape="gun")
        x, y = hand.landmarks[10]
        hand.landmarks[12] = (x, y - 20)
        self.assertFalse(is_gun(hand.landmarks))

    def test_ok_is_detected_and_is_not_gun(self):
        hand = make_hand(shape="ok")
        self.assertTrue(is_ok(hand.landmarks))
        self.assertFalse(is_gun(hand.landmarks))

    def test_separated_fingers_are_not_ok(self):
        hand = make_hand(shape="ok")
        x, y = hand.landmarks[4]
        hand.landmarks[4] = (x - 40, y + 20)
        self.assertFalse(is_ok(hand.landmarks))

    def test_folded_others_are_not_ok(self):
        hand = make_hand(shape="ok")
        hand.landmarks[12] = hand.landmarks[9]
        self.assertFalse(is_ok(hand.landmarks))


class TestSeek(unittest.TestCase):
    def test_left_back_forward_right_back_backward(self):
        self.assertEqual(play(gun(5, "Left")), [Command.SEEK_FORWARD_10])
        self.assertEqual(play(gun(5, "Right")), [Command.SEEK_BACK_10])

    def test_palm_side_gun_does_nothing(self):
        self.assertEqual(play(gun(10, "Left", palm=True)), [])
        self.assertEqual(play(gun(10, "Right", palm=True)), [])

    def test_holding_fires_once(self):
        self.assertEqual(play(gun(FPS * 3)), [Command.SEEK_FORWARD_10])

    def test_flicker_while_holding_fires_once(self):
        frames = (gun(8) + [[]]) * 12  # 8프레임마다 손을 놓침, 약 3.6초
        self.assertEqual(play(frames), [Command.SEEK_FORWARD_10])

    def test_label_flip_while_holding_does_not_fire_other_way(self):
        frames = (gun(6, "Left") + gun(6, "Right")) * 6  # 같은 손의 라벨이 흔들리는 경우
        self.assertEqual(play(frames), [Command.SEEK_FORWARD_10])

    def test_short_loss_does_not_rearm(self):
        frames = gun(5) + [[]] * 5 + gun(30)  # 약 0.17초 놓침
        self.assertEqual(play(frames), [Command.SEEK_FORWARD_10])

    def test_finger_fold_rearms(self):
        frames = gun(30) + still(FPS) + gun(5)
        self.assertEqual(play(frames), [Command.SEEK_FORWARD_10] * 2)

    def test_hand_gone_rearms(self):
        frames = gun(30) + [[]] * FPS + gun(5)
        self.assertEqual(play(frames), [Command.SEEK_FORWARD_10] * 2)

    def test_other_direction_after_release(self):
        frames = gun(5, "Left") + [[]] * FPS + gun(5, "Right")
        self.assertEqual(play(frames), [Command.SEEK_FORWARD_10, Command.SEEK_BACK_10])

    def test_quick_redo_during_cooldown_still_fires(self):
        frames = gun(5) + [[]] * 11 + gun(30)  # 0.37초 풀었다가 쿨다운 안에 다시 함
        self.assertEqual(play(frames), [Command.SEEK_FORWARD_10] * 2)

    def test_needs_stable_frames(self):
        self.assertEqual(play((gun(2) + still(1)) * 5), [])

    def test_two_hands_do_nothing(self):
        frames = [[make_hand(shape="gun", label="Left", palm=False, x=150),
                   make_hand(shape="gun", label="Right", palm=False, x=490)] for _ in range(15)]
        self.assertEqual(play(frames), [])


class TestPlayPause(unittest.TestCase):
    def test_ok_fires_once_while_held(self):
        self.assertEqual(play(ok(FPS * 3)), [Command.PLAY_PAUSE])

    def test_ok_needs_stable_frames(self):
        self.assertEqual(play((ok(2) + still(1)) * 5), [])

    def test_release_then_ok_again(self):
        self.assertEqual(play(ok(10) + still(FPS) + ok(10)), [Command.PLAY_PAUSE] * 2)


class TestVolume(unittest.TestCase):
    def test_up_needs_palm(self):
        self.assertEqual(play(still(5, gesture="Pointing_Up", palm=True)), [Command.VOLUME_UP])
        self.assertEqual(play(still(5, gesture="Pointing_Up", palm=False)), [])

    def test_down_needs_palm(self):
        self.assertEqual(play(still(5, gesture="Thumb_Down", palm=True)), [Command.VOLUME_DOWN])
        self.assertEqual(play(still(5, gesture="Thumb_Down", palm=False)), [])

    def test_holding_repeats(self):
        fired = play(still(FPS * 2, gesture="Pointing_Up"))  # 2초 유지, 0.5초 간격
        self.assertEqual(fired, [Command.VOLUME_UP] * 4)


class TestHandSide(unittest.TestCase):
    def test_all_four_cases(self):
        for label in ("Left", "Right"):
            self.assertEqual(hand_side(make_hand(label=label, palm=True)), "palm")
            self.assertEqual(hand_side(make_hand(label=label, palm=False)), "back")


def run_mode(frames, active=False):
    """프레임별 손 목록을 넣고 프레임별 active 값을 돌려준다."""
    state = RemoteState()
    state.active = active
    result = []
    for i, hands in enumerate(frames):
        now = 100 + i / FPS
        state.update_mode(now, hands)
        result.append(state.active)
    return result


def victory(n):
    return still(n, gesture="Victory")


class TestMode(unittest.TestCase):
    def test_victory_one_second_starts(self):
        result = run_mode(victory(FPS * 2))
        self.assertFalse(result[FPS - 5])
        self.assertTrue(result[-1])

    def test_short_victory_does_nothing(self):
        self.assertFalse(run_mode(victory(FPS // 2) + [[]] * FPS)[-1])

    def test_holding_toggles_once(self):
        self.assertTrue(all(run_mode(victory(FPS * 5))[FPS + 1:]))

    def test_release_then_victory_stops(self):
        result = run_mode(victory(FPS * 2) + still(FPS) + victory(FPS * 2))
        self.assertTrue(result[FPS * 3 - 1])
        self.assertFalse(result[-1])

    def test_label_flicker_keeps_counting(self):
        frames = (victory(8) + still(2)) * 5  # 10프레임마다 제스처 이름이 2프레임 흔들림
        self.assertTrue(run_mode(frames)[-1])

    def test_two_hands_victory_does_nothing(self):
        frames = [[make_hand(x=150, gesture="Victory"), make_hand(x=490, gesture="Victory", label="Left")]
                  for _ in range(FPS * 2)]
        self.assertFalse(run_mode(frames)[-1])

    def test_no_hand_returns_to_idle(self):
        state = RemoteState()
        state.active = True
        state.update_mode(10.0, [make_hand()])
        state.update_mode(16.0, [])
        self.assertFalse(state.active)


if __name__ == "__main__":
    unittest.main()
