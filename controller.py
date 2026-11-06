"""키 입력. 어느 창으로 갈지는 OS 가 정한다 = 지금 포커스된 창."""
from pynput.keyboard import Controller

keyboard = Controller()


def press(key):
    keyboard.tap(key)
