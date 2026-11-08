"""--test 모드 체크리스트. 제스처가 인식될 때마다 진행 상황을 출력한다."""
from .common import COMMAND_KO

ITEMS = ["시작", "종료", *COMMAND_KO.values()]


class Checklist:
    def __init__(self):
        self.passed = set()
        print("[테스트] 키는 보내지 않습니다. 확인할 동작: " + ", ".join(ITEMS))

    def mark(self, item):
        if item in self.passed:
            return
        self.passed.add(item)
        left = [name for name in ITEMS if name not in self.passed]
        print(f"[테스트] {item} 성공 ({len(self.passed)}/{len(ITEMS)})"
              + (f" 남은 동작: {', '.join(left)}" if left else " 전부 동작합니다!"), flush=True)
