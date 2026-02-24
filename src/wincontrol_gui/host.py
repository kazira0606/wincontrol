import asyncio
from contextlib import AsyncExitStack
import json
import sys

from PyQt5.QtCore import QObject, pyqtSignal
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, ListToolsResult
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


class Bridge(QObject):
    clear_signal = pyqtSignal()
    chat_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def clear_chat(self):
        """清除对话"""
        self.clear_signal.emit()

    def display_message(self, end: bool, role: str, content: str):
        """显示消息"""
        if content != None:
            self.chat_signal.emit({"end": end, "role": role, "content": content})

    def display_error(self, error: str):
        """显示错误"""
        if error != None:
            self.error_signal.emit(error)


class Host:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        # UI信号槽
        self.bridge = Bridge()

        # MCP Host
        self._server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "wincontrol_server.server"],
        )
        self._session = None

        # OpenAI Host
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model_name = model_name
        self._openai_tools = []

        # 对话上下文
        self._system_prompt = None
        self._messages = []

        # 资源上下文
        self._exit_stack = AsyncExitStack()
        self._initialized = False

    async def __aenter__(self):
        """初始化session"""
        if self._initialized:
            return

        read, write = await self._exit_stack.enter_async_context(
            stdio_client(self._server_params)
        )

        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._session.initialize()
        mcp_tools = await self._session.list_tools()
        self._openai_tools = self._mcp_tools_to_openai(mcp_tools)

        self._system_prompt = (
            (await self._session.get_prompt("system_prompt")).messages[0].content.text
        )
        self._messages.append({"role": "system", "content": self._system_prompt})

        self._initialized = True

    async def __aexit__(self):
        """退出session"""
        if not self._initialized:
            return
        await self._exit_stack.aclose()

        self._initialized = False

    def clear_chat(self):
        """清除对话"""
        self._messages = []
        self._messages.append(
            {
                "role": "system",
                "content": self._system_prompt,
            }
        )
        self.bridge.clear_chat()

    async def start_chat(self, user_input: str):
        """MCP循环"""
        screen_shot = (
            (await self._session.read_resource("screen://screenshot")).contents[0].blob
        )
        self._messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是最新的屏幕状态, 分析用户新的需求",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{screen_shot}"},
                    },
                    {
                        "type": "text",
                        "text": "如果要移动鼠标, 必须先调用screen_region_parser工具, 如果要操纵键盘, 必须先使用鼠标左键点击获取键盘焦点",
                    },
                ],
            }
        )
        self._messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )
        self.bridge.display_message(False, "user", user_input)

        # 循环执行
        while True:
            # 压缩历史图片消息并获取模型回复
            self._compress_messages()
            response = await self._get_response()
            assistant_output = response.choices[0].message
            assistant_output_msg = assistant_output.model_dump(exclude_none=True)
            self._messages.append(assistant_output_msg)

            if not ("tool_calls" in assistant_output_msg):
                # 模型无工具调用，结束任务
                self.bridge.display_message(
                    False, "reasoning", assistant_output_msg.get("reasoning_content")
                )
                self.bridge.display_message(
                    True, "assistant", assistant_output_msg.get("content")
                )
                return

            tool_call = assistant_output_msg.get("tool_calls")[0]
            tool_call_id = tool_call.get("id")

            # 显示模型回复
            self.bridge.display_message(
                False, "reasoning", assistant_output_msg.get("reasoning_content")
            )
            self.bridge.display_message(
                False, "assistant", assistant_output_msg.get("content")
            )

            args = tool_call.get("function").get("arguments")
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                self.bridge.display_error("工具参数解析错误")
                continue

            # 调用工具
            tool_call_result = await self._session.call_tool(
                tool_call.get("function").get("name"),
                args,
            )
            tool_message_content = self._mcp_tools_rsp_to_openai(tool_call_result)
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": tool_message_content,
            }
            self._messages.append(tool_message)

            # 等待1秒，确保工具调用完成
            await asyncio.sleep(1)

            if tool_call.get("function").get("name") != "screen_region_parser":
                # 除screen_region_parser工具外, 均需更新屏幕截图
                new_screen_shot = (
                    (await self._session.read_resource("screen://screenshot"))
                    .contents[0]
                    .blob
                )
                new_screen_shot_messages = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这是最新的屏幕状态, 指示了鼠标位置，先确认鼠标是否在正确位置，再确认上一步操作是否生效, 并继续完成任务",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{new_screen_shot}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "如果要移动鼠标, 必须先调用screen_region_parser工具, 如果要操纵键盘, 必须先使用鼠标左键点击获取键盘焦点",
                        },
                    ],
                }
                self._messages.append(new_screen_shot_messages)

    def _mcp_tools_to_openai(self, mcp_tools: ListToolsResult) -> list:
        """将 MCP tool list 转换为 OpenAI 格式"""
        openai_tools = []
        for mcp_tool in mcp_tools.tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": mcp_tool.name,
                    "description": mcp_tool.description,
                    "parameters": mcp_tool.inputSchema,
                },
            }
            openai_tools.append(openai_tool)
        return openai_tools

    def _mcp_tools_rsp_to_openai(self, rsp: CallToolResult) -> list:
        """将 MCP tool content 转换为 OpenAI 格式"""
        openai_content_list = []

        for item in rsp.content:
            if item.type == "text":
                openai_content_list.append({"type": "text", "text": item.text})

            elif item.type == "image":
                openai_content_list.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{item.mimeType};base64,{item.data}"
                        },
                    }
                )

            else:
                raise ValueError(f"Unknown content type: {item.type}")

        return openai_content_list

    async def _get_response(self) -> ChatCompletion:
        """OpenAI模型响应"""
        completion = await self._client.chat.completions.create(
            model=self._model_name,
            messages=self._messages,
            tools=self._openai_tools,
        )
        return completion

    def _compress_messages(self):
        """压缩消息，保留最新的 User 图片和 Tool 图片"""
        last_user_idx = -1
        last_tool_idx = -1

        # 1. 逆序寻找最新的 User 含图片的索引和 Tool 含图片的索引
        for msg_index, msg in enumerate(reversed(self._messages)):
            if (msg["role"] != "user" and msg["role"] != "tool") or isinstance(
                msg["content"], str
            ):
                continue
            if any(item["type"] == "image_url" for item in msg["content"]):
                if msg["role"] == "user" and last_user_idx == -1:
                    last_user_idx = len(self._messages) - 1 - msg_index
                elif msg["role"] == "tool" and last_tool_idx == -1:
                    last_tool_idx = len(self._messages) - 1 - msg_index
            if last_user_idx != -1 and last_tool_idx != -1:
                break

        # 2. 整个列表进行遍历压缩
        for msg_index, msg in enumerate(self._messages):
            if (msg["role"] != "user" and msg["role"] != "tool") or isinstance(
                msg["content"], str
            ):
                continue
            if msg_index == last_user_idx or msg_index == last_tool_idx:
                # 是最新的 User/Tool 图片，跳过不压缩
                continue
            if any(item.get("type") == "image_url" for item in msg["content"]):
                if msg["role"] == "user":
                    msg["content"] = [
                        {"type": "text", "text": "[此处为历史全屏截图且折叠无需关注]"}
                    ]
                elif msg["role"] == "tool":
                    msg["content"] = [
                        {
                            "type": "text",
                            "text": "[此处为历史screen_region_parser工具调用截图且已折叠无需关注]",
                        }
                    ]
