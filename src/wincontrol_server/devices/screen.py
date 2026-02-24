import mss
import numpy as np


class Screen:
    """屏幕类, 坐标从左上角(0, 0)开始到右小角(width-1, height-1)结束"""

    def __init__(self):
        self._sct = mss.mss()
        self._monitor = None

        for monitor in self._sct.monitors[1:]:
            if monitor["left"] == 0 and monitor["top"] == 0:
                self._monitor = monitor
                break

        if self._monitor is None:
            self._monitor = self._sct.monitors[1]

        self.left = self._monitor["left"]
        self.top = self._monitor["top"]
        self.width = self._monitor["width"]
        self.height = self._monitor["height"]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._sct.close()

    def capture(self) -> np.ndarray:
        """GUI截图, 返回形状为(height, width, 3)的BGR numpy数组"""
        mss_img = self._sct.grab(self._monitor)
        img = np.frombuffer(mss_img.bgra, dtype=np.uint8)
        img = img.reshape(mss_img.size[1], mss_img.size[0], 4)
        img = img[:, :, :3].copy()
        return img

    def capture_region(
        self, left: int, top: int, width: int, height: int
    ) -> np.ndarray:
        """GUI区域截图, 返回形状为(height, width, 3)的BGR numpy数组"""
        if (
            left < 0
            or top < 0
            or width <= 0
            or height <= 0
            or (left + width - 1) > self.width
            or (top + height - 1) > self.height
        ):
            raise ValueError("region out of screen or width/height <= 0")
        region = {
            "left": self.left + left,
            "top": self.top + top,
            "width": width,
            "height": height,
        }
        mss_img = self._sct.grab(region)
        img = np.frombuffer(mss_img.bgra, dtype=np.uint8)
        img = img.reshape(mss_img.size[1], mss_img.size[0], 4)
        img = img[:, :, :3].copy()
        return img
