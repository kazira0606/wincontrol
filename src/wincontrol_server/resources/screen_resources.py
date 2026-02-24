from pathlib import Path

import cv2
from mcp.server.fastmcp import FastMCP
import numpy as np

from wincontrol_server.devices.mouse import Mouse
from wincontrol_server.devices.screen import Screen


_SCRIPT_DIR = Path(__file__).parent
_POINTER_IMG = cv2.imread(str(_SCRIPT_DIR / "pointer.png"), cv2.IMREAD_UNCHANGED)
_POINTER_H, _POINTER_W = _POINTER_IMG.shape[:2]


def register(mcp: FastMCP):
    @mcp.resource("screen://screenshot", mime_type="image/png")
    def screen_shot() -> bytes:
        """获取当前屏幕截图"""
        with Screen() as screen:
            img_bgr = screen.capture()
            px, py = Mouse().position
            pw = _POINTER_W
            ph = _POINTER_H

            if px + pw > screen.width:
                pw = screen.width - px
            if py + ph > screen.height:
                ph = screen.height - py

            if pw <= 0 or ph <= 0:
                pass
            else:
                pointer = _POINTER_IMG[:ph, :pw]
                alpha = pointer[:, :, 3] / 255.0
                for c in range(3):
                    img_bgr[py : py + ph, px : px + pw, c] = (
                        alpha * pointer[:, :, c]
                        + (1 - alpha) * img_bgr[py : py + ph, px : px + pw, c]
                    ).astype(np.uint8)

            img_bgr = cv2.resize(
                img_bgr,
                (screen.width // 2, screen.height // 2),
                interpolation=cv2.INTER_AREA,
            )

            success, img = cv2.imencode(".png", img_bgr)
            if not success:
                raise ValueError("imencode failed")
            return img.tobytes()
