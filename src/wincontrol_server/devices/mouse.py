from pynput.mouse import Button, Controller


class Mouse:
    """鼠标类"""

    def __init__(self):
        self._mouse = Controller()

        self._BTNS = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
            "x1": Button.x1,
            "x2": Button.x2,
        }

    def _btn_parse(self, btn: str) -> Button:
        """解析按钮字符串"""
        if btn not in self._BTNS:
            raise ValueError(f"Invalid button: {btn}")
        return self._BTNS[btn]

    @property
    def position(self) -> tuple[int, int]:
        """获取鼠标位置"""
        return self._mouse.position

    def move(self, dx: int, dy: int) -> None:
        """移动鼠标"""
        self._mouse.move(dx, dy)

    def move_to(self, x: int, y: int) -> None:
        """移动鼠标到指定位置"""
        self._mouse.position = (x, y)

    def click(self, btn: str, count: int) -> None:
        """点击鼠标某键count次"""
        self._mouse.click(self._btn_parse(btn), count)

    def press(self, btn: str) -> None:
        """按住鼠标某键"""
        self._mouse.press(self._btn_parse(btn))

    def release(self, btn: str) -> None:
        """释放鼠标某键"""
        self._mouse.release(self._btn_parse(btn))

    def scroll(self, dx_step: int, dy_step: int) -> None:
        """滚动鼠标滚轮"""
        self._mouse.scroll(dx_step, dy_step)
