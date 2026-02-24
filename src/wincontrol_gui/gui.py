import asyncio
import sys
import threading

from PyQt5.QtCore import QObject, QSettings, QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QVBoxLayout,
    QWidget,
)

from wincontrol_gui.host import Host


# --------全局样式表 -------- #

GLOBAL_STYLE = """
/* -- 全局 -- */
QWidget {
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #24292e;
}

QWidget#MainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #eef1f5, stop:1 #e4e8ee
    );
}

/* -- 白色圆角卡片 -- */
QFrame#Card {
    background-color: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 12px;
}

/* -- 配置标签 -- */
QLabel#CfgLabel {
    font-size: 12px;
    font-weight: 600;
    color: #586069;
    min-width: 78px;
}

QLabel#PanelTitle {
    font-size: 15px;
    font-weight: 700;
    color: #24292e;
}

/* -- 配置输入框 -- */
QLineEdit#CfgInput {
    padding: 8px 14px;
    border: 2px solid #e1e4e8;
    border-radius: 8px;
    background-color: #fafbfc;
    font-size: 13px;
}
QLineEdit#CfgInput:focus  { border-color: #0366d6; background: #fff; }
QLineEdit#CfgInput:disabled { background: #f0f0f0; color: #999; }

/* -- 连接按钮 -- */
QPushButton#ConnBtn {
    padding: 9px 30px;
    border: none; border-radius: 8px;
    font-weight: 600; color: white;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0366d6, stop:1 #2188ff);
}
QPushButton#ConnBtn:hover   { background: #0256b9; }
QPushButton#ConnBtn:pressed { background: #024a9e; }
QPushButton#ConnBtn[connected="true"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #d73a49, stop:1 #e36270);
}
QPushButton#ConnBtn[connected="true"]:hover { background: #c42f3e; }

/* -- 聊天区 滚动条 -- */
QScrollArea#ChatScroll { border: none; background: transparent; }
QWidget#ChatContainer { background: transparent; }

QScrollArea#ChatScroll QScrollBar:vertical {
    width: 6px; background: transparent; margin: 4px 2px;
}
QScrollArea#ChatScroll QScrollBar::handle:vertical {
    background: #c1c8d0; border-radius: 3px; min-height: 30px;
}
QScrollArea#ChatScroll QScrollBar::handle:vertical:hover { background: #a0a8b4; }
QScrollArea#ChatScroll QScrollBar::add-line:vertical,
QScrollArea#ChatScroll QScrollBar::sub-line:vertical { height: 0; }

/* -- 用户气泡 -- */
QLabel#UserBubble {
    background-color: #0366d6;
    color: white;
    padding: 10px 16px;
    font-size: 16px;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    border-bottom-left-radius: 18px;
    border-bottom-right-radius: 5px;
}

/* -- 助手气泡 -- */
QLabel#AsstBubble {
    background-color: #f0f2f5;
    color: #24292e;
    padding: 10px 16px;
    font-size: 16px;
    border: 1px solid #e1e4e8;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 18px;
}

/* -- 推理气泡 -- */
QLabel#ReasoningBubble {
    background-color: #f0f2f5;
    color: #24292e;
    padding: 10px 16px;
    font-size: 14px;
    border: 1px solid #e1e4e8;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 18px;
}

/* -- 底部输入框 -- */
QLineEdit#ChatInput {
    padding: 10px 16px;
    border: 2px solid #e1e4e8;
    border-radius: 10px;
    background: #ffffff;
    font-size: 14px;
}
QLineEdit#ChatInput:focus    { border-color: #0366d6; }
QLineEdit#ChatInput:disabled { background: #f6f8fa; color: #999; }

/* -- 发送按钮 -- */
QPushButton#SendBtn {
    padding: 10px 24px; min-width: 72px;
    border: none; border-radius: 10px;
    font-weight: 600; color: white;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0366d6, stop:1 #2188ff);
}
QPushButton#SendBtn:hover    { background: #0256b9; }
QPushButton#SendBtn:pressed  { background: #024a9e; }
QPushButton#SendBtn:disabled { background: #c8d1d9; color: #f0f0f0; }
QPushButton#SendBtn[canceling="true"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e36209, stop:1 #f0883e);
}
QPushButton#SendBtn[canceling="true"]:hover { background: #d15704; }

/* -- 新对话按钮 -- */
QPushButton#ClearBtn {
    padding: 10px 20px; min-width: 72px;
    border: 2px solid #e1e4e8; border-radius: 10px;
    font-weight: 600; color: #586069; background: #fff;
}
QPushButton#ClearBtn:hover    { background: #f6f8fa; border-color: #c8d1d9; }
QPushButton#ClearBtn:pressed  { background: #edeff2; }
QPushButton#ClearBtn:disabled { border-color: #eee; color: #ccc; background: #fafafa; }
"""

# -------- 阴影辅助 -------- #


def _shadow(widget, blur=20, dy=2, alpha=30):
    s = QGraphicsDropShadowEffect(widget)
    s.setBlurRadius(blur)
    s.setOffset(0, dy)
    s.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(s)


# -------- 气泡 Widget -------- #


class BubbleWidget(QWidget):
    """聊天消息"""

    def __init__(self, text: str, role: str = "user", parent=None):
        if role not in {"user", "assistant", "reasoning"}:
            raise ValueError(f"Unknown role: {role}")

        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.setMaximumWidth(480)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        # -- 气泡文字 --
        self.label = QLabel(text)
        self.label.setTextFormat(Qt.PlainText)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if role == "user":
            self.label.setObjectName("UserBubble")
        elif role == "assistant":
            self.label.setObjectName("AsstBubble")
        else:
            self.label.setObjectName("ReasoningBubble")

        lay.addWidget(self.label)

        # -- 角色小字 --
        if role == "user":
            tag = QLabel("You")
        elif role == "assistant":
            tag = QLabel("✦ Assistant")
        else:
            tag = QLabel("✦ Reasoning")

        tag.setStyleSheet(
            f"font-size:10px; color:{'#8b949e' if role=='user' else '#0366d6'};"
            "background:transparent; border:none; padding:0 4px;"
        )
        if role == "user":
            tag.setAlignment(Qt.AlignRight)
        lay.addWidget(tag)


# -------- 聊天视图 -------- #


class ChatView(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatScroll")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._container.setObjectName("ChatContainer")
        self._lay = QVBoxLayout(self._container)
        self._lay.setContentsMargins(16, 16, 16, 16)
        self._lay.setSpacing(10)
        self._lay.setAlignment(Qt.AlignTop)

        # 占位提示
        self._placeholder = QLabel("💬  连接模型后即可开始对话")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(
            "color:#8b949e; font-size:14px; padding:60px 0; background:transparent;"
        )
        self._lay.addWidget(self._placeholder)

        self._lay.addStretch(1)
        self.setWidget(self._container)
        self._has_msg = False

    # -- 添加消息 --
    def add_message(self, text: str, role: str = "user"):
        if role not in {"user", "assistant", "reasoning"}:
            raise ValueError(f"Unknown role: {role}")

        if not self._has_msg:
            self._placeholder.hide()
            self._has_msg = True

        bubble = BubbleWidget(text, role)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if role == "user":
            row.addStretch(1)
            row.addWidget(bubble)
        elif role == "assistant":
            row.addWidget(bubble)
            row.addStretch(1)
        else:
            row.addWidget(bubble)
            row.addStretch(1)

        # 插在末尾 stretch 之前
        self._lay.insertLayout(self._lay.count() - 1, row)
        self._scroll_bottom()

    # -- 分隔线 --
    def add_divider(self):
        line = QLabel("── ✦ ──")
        line.setAlignment(Qt.AlignCenter)
        line.setStyleSheet(
            "color:#c8d1d9; font-size:11px; margin:6px 0; background:transparent;"
        )
        self._lay.insertWidget(self._lay.count() - 1, line)
        self._scroll_bottom()

    # -- 新对话提示 --
    def add_new_chat(self):
        tip = QLabel("──── 新对话开始  ────")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(
            "color:#8b949e; font-size:12px; letter-spacing:1px; margin:20px 0;"
            "background:transparent;"
        )
        self._lay.insertWidget(self._lay.count() - 1, tip)
        self._scroll_bottom()

    # -- 清空 --
    def clear_all(self):
        """只清空布局里的子项"""
        self._clear_layout(self._lay)
        # 重新加回末尾弹簧
        self._lay.addStretch(1)
        self._has_msg = True

    def _clear_layout(self, layout):
        """递归删除布局内所有 item"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            sub_layout = item.layout()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            elif sub_layout is not None:
                self._clear_layout(sub_layout)

    def _scroll_bottom(self):
        QTimer.singleShot(
            30,
            lambda: self.verticalScrollBar().setValue(
                self.verticalScrollBar().maximum()
            ),
        )


# -------- AsyncWorker -------- #


class AsyncWorker(QObject):
    """同步转异步模型调用"""

    def __init__(self, api_key, base_url, model_name):
        super().__init__()
        self._host = Host(api_key, base_url, model_name)
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._current_chat = None

    def start_chat(self, user_input: str):
        asyncio.run_coroutine_threadsafe(
            self._start_chat_wrapper(user_input), self._loop
        )

    def cancel_chat(self):
        asyncio.run_coroutine_threadsafe(self._cancel_chat_wrapper(), self._loop)

    def clear_chat(self):
        asyncio.run_coroutine_threadsafe(self._clear_chat_wrapper(), self._loop)

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._host.__aenter__())
        except Exception as e:
            self._host.bridge.display_error(f"MCP 初始化失败: {e}")
            self._loop.run_until_complete(self._host.__aexit__())
            self._loop.close()
            return
        self._loop.run_forever()
        self._loop.run_until_complete(self._host.__aexit__())
        self._loop.close()

    async def _start_chat_wrapper(self, user_input):
        self._current_chat = asyncio.current_task()
        try:
            await self._host.start_chat(user_input)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._host.bridge.display_error(f"对话错误: {str(e)}")
        finally:
            self._current_chat = None

    async def _cancel_chat_wrapper(self):
        if self._current_chat and not self._current_chat.done():
            self._current_chat.cancel()
            try:
                await self._current_chat
            except asyncio.CancelledError:
                pass

    async def _clear_chat_wrapper(self):
        if self._current_chat and not self._current_chat.done():
            self._current_chat.cancel()
            try:
                await self._current_chat
            except asyncio.CancelledError:
                pass
        try:
            self._host.clear_chat()
        except Exception as e:
            self._host.bridge.display_error(f"清除对话错误: {str(e)}")


# -------- 主窗口 -------- #


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("WinControl")
        self.resize(430, 860)
        self.setMinimumSize(600, 500)
        self.worker = None
        self._is_chatting = False
        self._init_ui()

    # -------- 构建 UI -------- #
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # -- 配置面板 --
        cfg_card = QFrame()
        cfg_card.setObjectName("Card")
        _shadow(cfg_card)
        cl = QVBoxLayout(cfg_card)
        cl.setContentsMargins(20, 16, 20, 18)
        cl.setSpacing(10)

        header = QHBoxLayout()
        self.status_dot = QLabel("⚪")
        self.status_dot.setStyleSheet("font-size:10px;")
        title = QLabel("连接配置")
        title.setObjectName("PanelTitle")
        header.addWidget(self.status_dot)
        header.addWidget(title)
        header.addStretch()
        self.btn_fold = QPushButton("收起 ▲")
        self.btn_fold.setFlat(True)
        self.btn_fold.setCursor(Qt.PointingHandCursor)
        self.btn_fold.setStyleSheet(
            "color:#586069;font-size:11px;padding:4px 8px;border:none;"
        )
        self.btn_fold.clicked.connect(self._toggle_fold)
        header.addWidget(self.btn_fold)
        cl.addLayout(header)

        self.cfg_body = QWidget()
        bl = QVBoxLayout(self.cfg_body)
        bl.setContentsMargins(0, 4, 0, 0)
        bl.setSpacing(8)
        self.entry_key = self._cfg_row(bl, "API Key")
        self.entry_key.setEchoMode(QLineEdit.Password)
        self.entry_key.setPlaceholderText("sk-......")
        self.entry_url = self._cfg_row(bl, "Base URL")
        self.entry_url.setPlaceholderText("https://api.openai.com/v1")
        self.entry_model = self._cfg_row(bl, "Model")
        self.entry_model.setPlaceholderText("gpt-5")
        cl.addWidget(self.cfg_body)

        btn_r = QHBoxLayout()
        btn_r.addStretch()
        self.btn_connect = QPushButton("  连  接  ")
        self.btn_connect.setObjectName("ConnBtn")
        self.btn_connect.setCursor(Qt.PointingHandCursor)
        self.btn_connect.clicked.connect(self.toggle_connection)
        btn_r.addWidget(self.btn_connect)
        btn_r.addStretch()
        cl.addLayout(btn_r)
        root.addWidget(cfg_card)

        # -- 聊天区和输入栏分割 --
        splitter = QSplitter(Qt.Vertical)

        # -- 聊天区 --
        chat_card = QFrame()
        chat_card.setObjectName("Card")
        _shadow(chat_card)
        chat_cl = QVBoxLayout(chat_card)
        chat_cl.setContentsMargins(0, 0, 0, 0)
        self.chat_view = ChatView()
        chat_cl.addWidget(self.chat_view)
        splitter.addWidget(chat_card)

        # -- 底部输入栏 --
        bar = QFrame()
        bar.setObjectName("Card")
        _shadow(bar, blur=14, dy=1)
        brl = QVBoxLayout(bar)
        brl.setContentsMargins(12, 10, 12, 10)
        brl.setSpacing(8)

        self.entry_input = QPlainTextEdit()
        self.entry_input.setObjectName("ChatInput")
        self.entry_input.setPlaceholderText("输入消息…")
        self.entry_input.setEnabled(False)
        brl.addWidget(self.entry_input, 1)

        btn = QHBoxLayout()
        self.btn_send = QPushButton("发 送")
        self.btn_send.setObjectName("SendBtn")
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.clicked.connect(self._on_action)
        self.btn_send.setEnabled(False)
        btn.addWidget(self.btn_send)

        self.btn_clear = QPushButton("新对话")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_context)
        self.btn_clear.setEnabled(False)
        btn.addWidget(self.btn_clear)
        brl.addLayout(btn)
        splitter.addWidget(bar)

        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        QTimer.singleShot(
            0, lambda s=splitter: s.setSizes([s.height() * 5 // 6, s.height() * 1 // 6])
        )
        root.addWidget(splitter, 1)

        # -------- 初始化 QSettings 并加载历史记录 -------- #
        self.settings = QSettings("WinControl", "WinControl")

        saved_key = self.settings.value("api_key", "")
        saved_url = self.settings.value("base_url", "")
        saved_model = self.settings.value("model", "")

        if saved_key:
            self.entry_key.setText(saved_key)
        if saved_url:
            self.entry_url.setText(saved_url)
        if saved_model:
            self.entry_model.setText(saved_model)

    def _cfg_row(self, parent_layout, text):
        r = QHBoxLayout()
        r.setSpacing(10)
        lb = QLabel(text)
        lb.setObjectName("CfgLabel")
        lb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lb.setFixedWidth(78)
        inp = QLineEdit()
        inp.setObjectName("CfgInput")
        r.addWidget(lb)
        r.addWidget(inp)
        parent_layout.addLayout(r)
        return inp

    def _toggle_fold(self):
        v = self.cfg_body.isVisible()
        self.cfg_body.setVisible(not v)
        self.btn_fold.setText("展开 ▼" if v else "收起 ▲")

    # -------- 按钮 -------- #

    def _on_action(self):
        if self._is_chatting:
            self._do_cancel()
        else:
            self._do_send()

    def _do_send(self):
        text = self.entry_input.toPlainText().strip()
        if not text or not self.worker:
            return
        self._is_chatting = True
        self.worker.start_chat(text)
        self.entry_input.clear()
        self.entry_input.setPlaceholderText("思考中……")
        self.entry_input.setEnabled(False)
        self.btn_send.setText("取 消")
        self.btn_send.setProperty("canceling", True)
        self.btn_send.style().unpolish(self.btn_send)
        self.btn_send.style().polish(self.btn_send)

    def _do_cancel(self):
        if self.worker:
            self.worker.cancel_chat()
        self._restore_ui()

    def _clear_context(self):
        if self.worker:
            self.worker.clear_chat()

    def _restore_ui(self):
        self._is_chatting = False
        self.entry_input.setPlaceholderText("输入消息…")
        self.entry_input.setEnabled(True)
        self.btn_send.setText("发 送")
        self.btn_send.setProperty("canceling", False)
        self.btn_send.style().unpolish(self.btn_send)
        self.btn_send.style().polish(self.btn_send)
        self.btn_send.setEnabled(True)
        self.entry_input.setFocus()

    # -------- 信号槽 -------- #

    def on_chat_message(self, data: dict):
        role = data.get("role")
        content = data.get("content")
        end = data.get("end")

        if content and role in ("user", "assistant"):
            self.chat_view.add_message(str(content), role)

        if content and role == "reasoning":
            self.chat_view.add_message(str(content), role)

        if end:
            self.chat_view.add_divider()
            self._restore_ui()

    def on_error(self, error_msg: str):
        msg = QMessageBox(self)
        msg.setWindowTitle("提示")
        msg.setText(error_msg)
        msg.setIcon(QMessageBox.Warning)
        msg.setStyleSheet(
            """
            QMessageBox { background:#fff; }
            QMessageBox QLabel { color:#24292e; font-size:13px; min-width:260px; }
            QPushButton { padding:6px 24px; border-radius:6px;
                          background:#0366d6; color:white; border:none; font-weight:600; }
            QPushButton:hover { background:#0256b9; }
        """
        )
        msg.exec_()
        self._restore_ui()
        self.entry_input.setPlaceholderText("发生错误，请重试…")

    def on_clear_confirmed(self):
        self.chat_view.clear_all()
        self.chat_view.add_new_chat()
        self._restore_ui()

    # -------- 连接管理 -------- #

    def toggle_connection(self):
        if self.worker is None:
            api_key = self.entry_key.text().strip()
            base_url = self.entry_url.text().strip()
            model = self.entry_model.text().strip()
            if not all([api_key, base_url, model]):
                self.on_error("请完整填写 API Key、Base URL 和 Model")
                return
            try:
                self._set_cfg_enabled(False)
                self.worker = AsyncWorker(api_key, base_url, model)
                bridge = self.worker._host.bridge
                bridge.chat_signal.connect(self.on_chat_message)
                bridge.error_signal.connect(self.on_error)
                bridge.clear_signal.connect(self.on_clear_confirmed)

                self.btn_connect.setText("  断开连接  ")
                self.btn_connect.setProperty("connected", True)
                self.btn_connect.style().unpolish(self.btn_connect)
                self.btn_connect.style().polish(self.btn_connect)
                self.status_dot.setText("🟢")

                self.entry_input.setEnabled(True)
                self.btn_send.setEnabled(True)
                self.btn_clear.setEnabled(True)
                self.entry_input.setFocus()
                self.cfg_body.setVisible(False)
                self.btn_fold.setText("展开 ▼")
            except Exception as e:
                self._set_cfg_enabled(True)
                self.on_error(f"初始化失败: {e}")
                self.worker = None
        else:
            self.worker.stop()
            self.worker = None
            self._is_chatting = False

            self._set_cfg_enabled(True)
            self.btn_connect.setText("  连  接  ")
            self.btn_connect.setProperty("connected", False)
            self.btn_connect.style().unpolish(self.btn_connect)
            self.btn_connect.style().polish(self.btn_connect)
            self.status_dot.setText("⚪")

            self.entry_input.setEnabled(False)
            self.btn_send.setText("发 送")
            self.btn_send.setEnabled(False)
            self.btn_clear.setEnabled(False)
            self.cfg_body.setVisible(True)
            self.btn_fold.setText("收起 ▲")

    def _set_cfg_enabled(self, on: bool):
        self.entry_key.setEnabled(on)
        self.entry_url.setEnabled(on)
        self.entry_model.setEnabled(on)

    def closeEvent(self, event):
        if hasattr(self, "settings"):
            self.settings.setValue("api_key", self.entry_key.text().strip())
            self.settings.setValue("base_url", self.entry_url.text().strip())
            self.settings.setValue("model", self.entry_model.text().strip())

        if self.worker:
            self.worker.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setStyleSheet(GLOBAL_STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


# -------- 启动 -------- #
if __name__ == "__main__":
    main()
