from pathlib import Path

from mcp.server.fastmcp import FastMCP

from wincontrol_server.devices.screen import Screen


def register(mcp: FastMCP):
    @mcp.prompt()
    def system_prompt() -> str:
        """获取系统提示"""
        with Screen() as screen:
            screen_w = screen.width
            screen_h = screen.height
            U_MAX = 1000
            V_MAX = int(1000 / screen_w * screen_h)
            PROMPTS_DIR = Path(__file__).parent
            with open(PROMPTS_DIR / "system_prompt.md", "r", encoding="utf-8") as f:
                template = f.read()
                return template.format(U_MAX=U_MAX, V_MAX=V_MAX)
