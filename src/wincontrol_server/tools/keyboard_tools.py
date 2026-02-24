from enum import StrEnum
import time

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from wincontrol_server.devices.keyboard import Keyboard


class SpecialKey(StrEnum):
    """特殊按键"""

    CTRL = "ctrl"
    SHIFT = "shift"
    ALT = "alt"
    WIN = "win"
    ESC = "esc"
    BACKSPACE = "backspace"
    TAB = "tab"
    CAPS_LOCK = "caps_lock"
    ENTER = "enter"
    SPACE = "space"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"
    END = "end"
    HOME = "home"
    LEFT = "left"
    UP = "up"
    RIGHT = "right"
    DOWN = "down"


class ShortcutKey(StrEnum):
    """快捷键"""

    CTRL_A = "ctrl+a"
    CTRL_C = "ctrl+c"
    CTRL_V = "ctrl+v"
    CTRL_X = "ctrl+x"
    CTRL_Z = "ctrl+z"


def register(mcp: FastMCP):
    @mcp.tool()
    def type_str(text: str) -> dict:
        """在当前鼠标焦点的输入框中输入一段文本(中文/英文/数字)"""
        kb = Keyboard()
        try:
            kb.type_str(text)
            return TextContent(
                type="text",
                text=f"typed: {text}",
            )
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )

    @mcp.tool()
    def tap_special_key(key: SpecialKey) -> dict:
        """敲击指定的单个特殊按键"""
        kb = Keyboard()
        try:
            kb.tap(key)
            return TextContent(
                type="text",
                text=f"pressed: {key}",
            )
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )

    @mcp.tool()
    def tap_normal_key(key: str) -> dict:
        """敲击指定的单个普通按键"""
        if len(key) != 1:
            return TextContent(
                type="text",
                text=f"error: {key} is not a normal key",
            )
        kb = Keyboard()
        try:
            kb.tap(key)
            return TextContent(
                type="text",
                text=f"pressed: {key}",
            )
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )

    @mcp.tool()
    def tap_shortcut(shortcut: ShortcutKey) -> dict:
        """敲击指定的快捷键"""
        kb = Keyboard()
        keys = shortcut.split("+")
        try:
            for key in keys:
                kb.press(key)

            time.sleep(0.05)

            for key in keys:
                kb.release(key)
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )
