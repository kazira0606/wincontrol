import ctypes

from mcp.server.fastmcp import FastMCP

from wincontrol_server.prompts import prompts
from wincontrol_server.resources import screen_resources
from wincontrol_server.tools import mouse_tools
from wincontrol_server.tools import keyboard_tools
from wincontrol_server.tools import screen_tools


def enable_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def main():
    enable_dpi_awareness()

    mcp = FastMCP("wincontrol", json_response=True)

    prompts.register(mcp)
    screen_resources.register(mcp)
    mouse_tools.register(mcp)
    keyboard_tools.register(mcp)
    screen_tools.register(mcp)

    mcp.run()


if __name__ == "__main__":
    main()
