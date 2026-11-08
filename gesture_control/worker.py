"""유튜브 제어를 별도 스레드에서 처리한다 (조하연 구조를 줄임).

창 포커스에 시간이 걸려도 웹캠과 인식이 멈추지 않게 하기 위해서다.
명령이 없는 동안에는 유튜브 탭과 플레이어를 미리 찾아 둔다 (읽기만 하고 포커스는 바꾸지 않음).
"""
import queue
import threading
import time

from .common import COMMAND_KO
from .controller import YouTubeController, select_target
from .youtube_target import STAGE_TARGET, VIDEO, UIABackend, _wait, activate_window, foreground_hwnd

COMMAND_MAX_WAIT = 2.0  # 이보다 오래 기다린 명령은 보내지 않는다 (늦은 실행 방지)
WARM_UP_SEC = 3.0       # 명령이 없으면 이 간격으로 유튜브 탭·플레이어를 미리 찾는다


class FastBackend(UIABackend):
    """플레이어를 이미 찾아 두었으면 창·탭 재검사(약 1.7초)를 건너뛰고 바로 포커스를 준다."""

    def prepare(self, target):
        player = self._player_cache.get((target.hwnd, target.tab_id))
        if player is None or not self._player_visible(player):  # 탭이 바뀌었으면 원래 방식으로
            return super().prepare(target)
        if foreground_hwnd() != target.hwnd and not activate_window(target.hwnd)[0]:
            return super().prepare(target)
        if not self._focus_in_player(player):
            try:
                player.SetFocus()  # 클릭이 아니라 포커스만 옮김 -> 재생/정지 변화 없음
            except Exception:
                pass
            if not _wait(lambda: self._focus_in_player(player), 0.7):
                return super().prepare(target)
        if foreground_hwnd() != target.hwnd:
            return super().prepare(target)
        return True, "", "빠른 준비"

    def warm_up(self, target):
        """보이는 영상 탭이면 플레이어를 미리 찾아 둔다 (읽기 전용)."""
        if target.page == VIDEO and target.selected and (target.hwnd, target.tab_id) not in self._player_cache:
            self._find_player(target, timeout=0.5)


def pick_target(backend):
    """영상 페이지를 우선으로 첫 번째 유튜브 대상을 고른다."""
    targets = backend.find_targets()
    videos = [t for t in targets if t.page == VIDEO]
    return (videos or targets or [None])[0]


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
                try:
                    command, asked_at = self.jobs.get(timeout=WARM_UP_SEC)
                except queue.Empty:
                    self._warm_up(controller, backend)
                    continue
                self._execute(controller, backend, command, asked_at)

    @staticmethod
    def _warm_up(controller, backend):
        try:
            if controller.target is None:
                controller.target = pick_target(backend)
                if controller.target:
                    print(f"  제어 대상을 찾았습니다: {controller.target.describe()}", flush=True)
            if controller.target:
                backend.warm_up(controller.target)
        except Exception:
            pass  # 미리 찾기는 실패해도 명령 때 다시 시도한다

    @staticmethod
    def _execute(controller, backend, command, asked_at):
        waited = time.monotonic() - asked_at
        if waited > COMMAND_MAX_WAIT:
            print(f"  [취소] {COMMAND_KO[command]}: {waited:.1f}초 기다려 보내지 않음", flush=True)
            return
        if controller.target is None:
            controller.target = pick_target(backend)
        result = controller.execute(command)
        took = time.monotonic() - asked_at
        print(f"  {result.message} ({took:.1f}초)", flush=True)
        if result.stage == STAGE_TARGET:  # 탭이 닫혔으면 다음 명령 때 다시 찾는다
            controller.target = None
