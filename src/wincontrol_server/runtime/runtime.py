from wincontrol_server.devices.screen import Screen


def coord_to_screen(screen: Screen, u: int, v: int) -> tuple[int, int]:
    """将归一化坐标(x轴统一为1到1000)转换为屏幕坐标"""
    screen_w = screen.width
    screen_h = screen.height
    screen_left = screen.left
    screen_top = screen.top

    U_MAX = 1000
    V_MAX = int(1000 / screen_w * screen_h)

    u = max(1, min(u, U_MAX))
    v = max(1, min(v, V_MAX))

    x = int(u / U_MAX * screen_w)
    y = int(v / V_MAX * screen_h)

    x_real = max(screen_left, min(screen_left + x, screen_left + screen_w - 1))
    y_real = max(screen_top, min(screen_top + y, screen_top + screen_h - 1))

    return (x_real, y_real)


def screen_to_coord(screen: Screen, x: int, y: int) -> tuple[int, int]:
    """将屏幕坐标转换为归一化坐标(x轴统一为1到1000)"""
    screen_w = screen.width
    screen_h = screen.height
    screen_left = screen.left
    screen_top = screen.top

    U_MAX = 1000
    V_MAX = int(1000 / screen_w * screen_h)

    x = x - screen_left
    y = y - screen_top

    x = max(0, min(x, screen_w - 1))
    y = max(0, min(y, screen_h - 1))

    u = int(x / (screen_w - 1) * U_MAX)
    v = int(y / (screen_h - 1) * V_MAX)

    return (max(1, u), max(1, v))
