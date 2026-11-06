"""IDLE/ACTIVE 상태 전환과 오작동 필터(연속 프레임 + 쿨다운)."""
import config
from gestures import both_hands


class RemoteState:
    def __init__(self):
        self.mode = "IDLE"
        self.hold_since = None
        self.last_seen = 0.0
        self.last_command = None
        self.streak = 0
        self.cool_until = 0.0

    def update_mode(self, now, hands):
        if hands:
            self.last_seen = now

        if self.mode == "ACTIVE" and now - self.last_seen > config.NO_HAND_SEC:
            self._switch("IDLE")
            return

        wanted = "Open_Palm" if self.mode == "IDLE" else "Closed_Fist"
        if not both_hands(hands, wanted):
            self.hold_since = None
            return

        if self.hold_since is None:
            self.hold_since = now
        if now - self.hold_since >= config.HOLD_SEC:
            self._switch("ACTIVE" if self.mode == "IDLE" else "IDLE")

    def should_fire(self, command, now):
        if command != self.last_command:
            self.last_command = command
            self.streak = 0
        if command is None:
            return False

        self.streak += 1
        # 쓸기는 이미 일정 시간의 이동량으로 판정했으므로 첫 프레임에 바로 인정한다
        needed = config.STABLE_FRAMES if command == "OK" else 1
        # == 로 비교: OK 를 계속 들고 있어도 키는 한 번만 나간다 (손을 풀어야 다시 가능)
        if self.streak == needed and now >= self.cool_until:
            self.cool_until = now + config.COOLDOWN_SEC
            return True
        return False

    def _switch(self, mode):
        self.mode = mode
        self.hold_since = None
        self.last_command = None
        self.streak = 0
