"""유튜브 제어를 별도 스레드에서 처리한다 (조하연 구조를 줄임).

창 포커스와 확인에 시간이 걸려도 웹캠과 인식이 멈추지 않게 하기 위해서다.
"""
import queue
import threading
import time

from .common import COMMAND_KO
from .controller import YouTubeController, select_target
from .youtube_target import STAGE_TARGET, UIABackend, foreground_hwnd

COMMAND_MAX_WAIT = 2.0  # 이보다 오래 기다린 명령은 보내지 않는다 (늦은 실행 방지)


class FastBackend(UIABackend):
    """이미 유튜브 플레이어에 포커스가 있으면 창·탭 재검사(약 1.7초)를 건너뛴다."""

    def prepare(self, target):
        player = self._player_cache.get((target.hwnd, target.tab_id))
        if player is not None and foreground_hwnd() == target.hwnd and self._focus_in_player(player):
            return True, "", "포커스 유지"
        return super().prepare(target)


class ControlWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.jobs = queue.Queue()
        self.ready = threading.Event()

    def submit(self, command):
        self.jobs.put((command, time.monotonic()))

    def run(self):
        import uiautomation as auto  # UI Automation 은 쓰는 스레드에서 초기화해야 한다

        with auto.UIAutomationInitializerInThread():
            backend = FastBackend()
            controller = YouTubeController(live=True, backend=backend, target=select_target(backend), verify=False)
            self.ready.set()
            while True:
                command, asked_at = self.jobs.get()
                self._execute(controller, backend, command, asked_at)

    @staticmethod
    def _execute(controller, backend, command, asked_at):
        waited = time.monotonic() - asked_at
        if waited > COMMAND_MAX_WAIT:
            print(f"  [취소] {COMMAND_KO[command]}: {waited:.1f}초 기다려 보내지 않음", flush=True)
            return
        if controller.target is None:  # 시작할 때 유튜브가 없었으면 지금 다시 찾는다
            targets = backend.find_targets()
            controller.target = targets[0] if targets else None
        result = controller.execute(command)
        took = time.monotonic() - asked_at
        print(f"  {result.message} ({took:.1f}초)", flush=True)
        if result.stage == STAGE_TARGET:  # 탭이 닫혔으면 다음 명령 때 다시 찾는다
            controller.target = None
