"""대기/인식 중 상태 전환과 오작동 필터(연속 프레임 + 쿨다운)."""
from . import config
from .common import Command
from .gestures import OnceGate, is_victory

VOLUME = (Command.VOLUME_UP, Command.VOLUME_DOWN)


class RemoteState:
    def __init__(self):
        self.active = False
        self.hold_since = None
        self.victory_gate = OnceGate()
        self.last_seen = 0.0
        self.last_command = None
        self.streak = 0
        self.cool_until = 0.0

    def update_mode(self, now, hands):
        if hands:
            self.last_seen = now

        if self.active and now - self.last_seen > config.NO_HAND_SEC:
            self._switch(False)
            return

        victory = is_victory(hands)
        self.victory_gate.update(victory, now)
        # 제스처 이름이 한두 프레임 흔들려도 유지 시간을 처음부터 다시 세지 않는다
        if now - self.victory_gate.seen >= config.RELEASE_SEC:
            self.hold_since = None
        if not victory or self.victory_gate.locked:
            return

        if self.hold_since is None:
            self.hold_since = now
        if now - self.hold_since >= config.HOLD_SEC:
            self.victory_gate.locked = True  # 브이를 풀어야 다시 전환된다
            self._switch(not self.active)

    def next_command(self, reader, hands, now):
        """이번 프레임에 실제로 보낼 명령. 없으면 None."""
        command = reader.update(hands, now)
        if not self.should_fire(command, now):
            return None
        reader.lock(command)
        return command

    def should_fire(self, command, now):
        if command != self.last_command:
            self.last_command = command
            self.streak = 0
        if command is None:
            return False

        self.streak += 1
        if self.streak < config.STABLE_FRAMES or now < self.cool_until:
            return False

        # 볼륨은 자세를 유지하는 동안 일정 간격으로 반복한다
        self.cool_until = now + (config.VOLUME_REPEAT_SEC if command in VOLUME else config.COOLDOWN_SEC)
        return True

    def _switch(self, active):
        self.active = active
        self.hold_since = None
        self.last_command = None
        self.streak = 0
