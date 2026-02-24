import time

from pynput.keyboard import Controller, Key
import pyperclip


class Keyboard:
    """键盘类"""

    def __init__(self):
        self._keyboard = Controller()

        self._KEYS = {
            "ctrl": Key.ctrl,
            "shift": Key.shift,
            "alt": Key.alt,
            "win": Key.cmd,
            "esc": Key.esc,
            "backspace": Key.backspace,
            "tab": Key.tab,
            "caps_lock": Key.caps_lock,
            "enter": Key.enter,
            "space": Key.space,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "end": Key.end,
            "home": Key.home,
            "left": Key.left,
            "up": Key.up,
            "right": Key.right,
            "down": Key.down,
        }

    def _key_parse(self, key: str) -> Key:
        """解析按键字符串"""
        # 特殊按键
        if key in self._KEYS:
            return self._KEYS[key]
        # 普通字符键
        if len(key) == 1:
            return key
        # 其他情况
        raise ValueError(f"Invalid key: {key}")

    def type_str(self, text: str):
        """输入一段字符串文本"""
        pyperclip.copy(text)
        self._keyboard.press(Key.ctrl)
        self._keyboard.press("v")
        time.sleep(0.05)
        self._keyboard.release(Key.ctrl)
        self._keyboard.release("v")

    def press(self, key: str) -> None:
        """按住某键"""
        self._keyboard.press(self._key_parse(key))

    def release(self, key: str) -> None:
        """释放某键"""
        self._keyboard.release(self._key_parse(key))

    def tap(self, key: str) -> None:
        """点击某键1次"""
        self._keyboard.press(self._key_parse(key))
        time.sleep(0.05)
        self._keyboard.release(self._key_parse(key))
