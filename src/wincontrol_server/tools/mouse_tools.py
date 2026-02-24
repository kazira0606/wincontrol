import time

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from wincontrol_server.devices.mouse import Mouse
from wincontrol_server.devices.screen import Screen
from wincontrol_server.runtime.runtime import (
    coord_to_screen,
    screen_to_coord,
)


def register(mcp: FastMCP):
    @mcp.tool()
    def pointer_move_to(u: int, v: int) -> dict:
        """将鼠标指针移动到归一化坐标(u,v)"""
        mouse = Mouse()
        with Screen() as screen:
            try:
                mouse.move_to(*coord_to_screen(screen, u, v))
                new_u, new_v = screen_to_coord(screen, *mouse.position)
                return TextContent(
                    type="text",
                    text=f"({new_u}, {new_v})",
                )
            except Exception as e:
                return TextContent(
                    type="text",
                    text=f"error: {str(e)}",
                )

    @mcp.tool()
    def left_click() -> dict:
        """点击鼠标左键1次"""
        mouse = Mouse()
        try:
            mouse.click("left", 1)
            return TextContent(
                type="text",
                text="success",
            )
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )

    @mcp.tool()
    def right_click() -> dict:
        """点击鼠标右键1次"""
        mouse = Mouse()
        try:
            mouse.click("right", 1)
            return TextContent(
                type="text",
                text="success",
            )
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )


    @mcp.tool()
    def left_double_click() -> dict:
        """双击鼠标左键"""
        mouse = Mouse()
        try:
            mouse.click("left", 2)
            return TextContent(
                type="text",
                text="success",
            )
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )

    @mcp.tool()
    def left_drag(u: int, v: int) -> dict:
        """按住鼠标左键从当前归一化坐标拖拽到归一化坐标(u,v)"""
        mouse = Mouse()
        with Screen() as screen:
            current_x, current_y = mouse.position
            aim_x, aim_y = coord_to_screen(screen, u, v)
            try:
                mouse.press("left")
                steps = 60
                for i in range(steps):
                    curr_x = int(current_x + (aim_x - current_x) * ((i + 1) / steps))
                    curr_y = int(current_y + (aim_y - current_y) * ((i + 1) / steps))
                    mouse.move_to(curr_x, curr_y)
                    time.sleep(0.005)
                mouse.move_to(aim_x, aim_y)
                mouse.release("left")
                return TextContent(
                    type="text",
                    text=f"({u}, {v})",
                )

            except Exception as e:
                try:
                    mouse.left_release()
                except:
                    pass
                return TextContent(
                    type="text",
                    text=f"error: {str(e)}",
                )

    @mcp.tool()
    def wheel_scroll(dx_step: int, dy_step: int) -> dict:
        """滚动鼠标滚轮(dx_step,dy_step)步"""
        mouse = Mouse()
        try:
            mouse.scroll(dx_step, dy_step)
            return TextContent(
                type="text",
                text=f"({dx_step}, {dy_step})",
            )
        except Exception as e:
            return TextContent(
                type="text",
                text=f"error: {str(e)}",
            )
