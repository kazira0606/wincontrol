import base64
from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path

import cv2
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent
import numpy as np
import onnxruntime as ort

from wincontrol_server.devices.screen import Screen
from wincontrol_server.runtime.runtime import screen_to_coord


class Region(StrEnum):
    """屏幕区域"""

    LEFT_UP = "left_up"
    LEFT_MID = "left_mid"
    LEFT_DOWN = "left_down"
    MID_UP = "mid_up"
    MID_MID = "mid_mid"
    MID_DOWN = "mid_down"
    RIGHT_UP = "right_up"
    RIGHT_MID = "right_mid"
    RIGHT_DOWN = "right_down"


@dataclass
class ParsedResult:
    """解析结果"""

    parsed_img: np.ndarray
    boxes: dict[int, tuple[int, int]]


class Omini:
    """GUI Parser"""

    def __init__(
        self,
        model_path: str,
        conf: float = 0.05,
        iou: float = 0.1,
        overlap: float = 0.3,
    ):
        self._conf = conf
        self._iou = iou
        self._overlap = overlap

        self._session = ort.InferenceSession(
            model_path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )

        input_data = self._session.get_inputs()[0]
        self._input_name = input_data.name
        self._input_l = input_data.shape[2]

    def parse(self, left: int, top: int, img: np.ndarray) -> ParsedResult:
        """解析GUI, 形参为解析区域起始坐标和BGR numpy数组"""
        img_h = img.shape[0]
        img_w = img.shape[1]

        proc_img, ratio, (region_left, region_top) = self._preprocess(img)
        outputs = self._session.run(None, {self._input_name: proc_img})[0][
            0
        ].T  # outputs每一行是一个检测框
        boxes_raw = outputs[:, :4]  # [cx, cy, w, h]
        scores = outputs[:, 4]  # 置信度

        # 1. 过滤置信度
        idx = scores > self._conf
        if not idx.any():
            return img  # 没有检测到任何框, 直接返回原图
        boxes_raw, scores = boxes_raw[idx], scores[idx]

        # 2. 过滤IOU
        idx = self._nms(boxes_raw, scores)
        boxes_raw, scores = boxes_raw[idx], scores[idx]

        # 3. 过滤重叠框
        idx = self._overlap_nms(boxes_raw)
        boxes_raw, scores = boxes_raw[idx], scores[idx]

        # 4. 坐标还原
        boxes = np.stack(
            [
                (boxes_raw[:, 0] - boxes_raw[:, 2] / 2 - region_left) / ratio,
                (boxes_raw[:, 1] - boxes_raw[:, 3] / 2 - region_top) / ratio,
                (boxes_raw[:, 0] + boxes_raw[:, 2] / 2 - region_left) / ratio,
                (boxes_raw[:, 1] + boxes_raw[:, 3] / 2 - region_top) / ratio,
            ],
            axis=1,
        )

        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, img_w)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, img_h)

        # 5. 过滤极小框
        # 计算每个框的宽度和高度
        widths = boxes[:, 2] - boxes[:, 0]
        heights = boxes[:, 3] - boxes[:, 1]

        # 过滤条件：宽度和高度必须都大于 10 像素
        keep = (widths > 10) & (heights > 10)
        boxes = boxes[keep]

        # 6. 画框
        drawed_img = self._draw(img, boxes)

        # 7. 构造归一化坐标结果
        boxes_center = np.round((boxes[:, :2] + boxes[:, 2:]) / 2).astype(int)
        boxes_center[:, 0] += left
        boxes_center[:, 1] += top

        with Screen() as screen:
            boxes_map = {
                i: screen_to_coord(screen, x, y)
                for i, (x, y) in enumerate(boxes_center)
            }

        return ParsedResult(drawed_img, boxes_map)

    def _preprocess(
        self, image: np.ndarray
    ) -> tuple[np.ndarray, float, tuple[int, int]]:
        """预处理图像, 返回RGB numpy数组"""
        img_h = image.shape[0]
        img_w = image.shape[1]

        ratio = self._input_l / max(img_w, img_h)
        if img_w > img_h:
            new_w = self._input_l
            new_h = round(img_h * ratio)
        else:
            new_w = round(img_w * ratio)
            new_h = self._input_l
        resized = cv2.resize(image, (new_w, new_h))

        pad_w = (self._input_l - new_w) / 2
        pad_h = (self._input_l - new_h) / 2

        top = int(np.floor(pad_h))
        bottom = int(np.ceil(pad_h))
        left = int(np.floor(pad_w))
        right = int(np.ceil(pad_w))

        padded = cv2.copyMakeBorder(
            resized,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=(114, 114, 114),
        )

        proc_img = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        proc_img = proc_img.transpose(2, 0, 1)[np.newaxis]
        return np.ascontiguousarray(proc_img), ratio, (left, top)

    def _nms(self, boxes_raw: np.ndarray, scores: np.ndarray) -> np.ndarray:
        """去重, 返回保留框的索引"""
        x1 = boxes_raw[:, 0] - (boxes_raw[:, 2] / 2)
        y1 = boxes_raw[:, 1] - (boxes_raw[:, 3] / 2)
        x2 = boxes_raw[:, 0] + (boxes_raw[:, 2] / 2)
        y2 = boxes_raw[:, 1] + (boxes_raw[:, 3] / 2)

        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)
            if order.size == 1:
                break

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
            order = order[np.where(iou <= self._iou)[0] + 1]

        return np.array(keep, dtype=np.int64)

    def _overlap_nms(self, boxes_raw: np.ndarray) -> np.ndarray:
        """过滤重叠框: 当大框包小框（交集占小框比例超阈值）时，去掉大框，保留小框。返回保留框的索引"""
        if len(boxes_raw) == 0:
            return np.array([], dtype=np.int64)

        x1 = boxes_raw[:, 0] - boxes_raw[:, 2] / 2
        y1 = boxes_raw[:, 1] - boxes_raw[:, 3] / 2
        x2 = boxes_raw[:, 0] + boxes_raw[:, 2] / 2
        y2 = boxes_raw[:, 1] + boxes_raw[:, 3] / 2
        areas = (x2 - x1) * (y2 - y1)

        order = areas.argsort()
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)

            if order.size == 1:
                break

            # 计算当前最小框，与剩余所有的框的交集坐标
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            # 计算交集面积
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            inter = w * h

            iom = inter / (areas[i] + 1e-6)

            inds = np.where(iom <= self._overlap)[0]

            order = order[inds + 1]

        return np.array(keep, dtype=np.int64)

    def _draw(self, img: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)

            label = str(i)
            font_scale = 0.5
            thickness = 1
            (tw, th), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )

            # 标签尺寸
            padding = 1
            bg_w = tw + padding * 2
            bg_h = th + padding * 2

            # 计算面积比例（标签原始面积 / 框面积）
            box_area = (x2 - x1) * (y2 - y1)
            label_area = bg_w * bg_h

            # 默认位置框内左上角
            bg_x1 = x1
            bg_y1 = y1
            text_x = x1 + padding
            text_y = y1 + bg_h - padding  # 文字基线在背景框底部

            # 如果占用超过10%，尝试放到框外
            if label_area > box_area * 0.10:
                # 计算框外位置
                out_y1 = y1 - bg_h

                # 如果没有超出图片上边界，则使用框外位置
                if out_y1 >= 0:
                    bg_y1 = out_y1
                    text_y = y1 - padding

            # 绘制标签背景和文字
            bg_x2 = bg_x1 + bg_w
            bg_y2 = bg_y1 + bg_h

            cv2.rectangle(img, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 255, 0), -1)
            cv2.putText(
                img,
                label,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (0, 0, 0),
                thickness,
                lineType=cv2.LINE_AA,
            )
        return img


_SCRIPT_DIR = Path(__file__).parent
_OMINI = Omini(str(_SCRIPT_DIR / "omini.onnx"))


def register(mcp: FastMCP):
    @mcp.tool()
    def screen_region_parser(
        region: Region,
    ) -> list:
        """解析指定屏幕区域的GUI元素, 返回添加了标注框的图片和标注框索引及其对应框的归一化坐标。"""
        with Screen() as screen:
            REGION_START_MAP = {
                Region.LEFT_UP: (0, 0),
                Region.LEFT_MID: (0, screen.height // 4),
                Region.LEFT_DOWN: (0, screen.height // 2),
                Region.MID_UP: (screen.width // 4, 0),
                Region.MID_MID: (screen.width // 4, screen.height // 4),
                Region.MID_DOWN: (screen.width // 4, screen.height // 2),
                Region.RIGHT_UP: (screen.width // 2, 0),
                Region.RIGHT_MID: (screen.width // 2, screen.height // 4),
                Region.RIGHT_DOWN: (screen.width // 2, screen.height // 2),
            }

            left, top = REGION_START_MAP[region]
            width = screen.width // 2
            height = screen.height // 2

            img_bgr = screen.capture_region(left, top, width, height)
            parsed_result = _OMINI.parse(left, top, img_bgr)

            parsed_img = parsed_result.parsed_img
            parsed_boxes = parsed_result.boxes

            success, img = cv2.imencode(".png", parsed_img)
            if not success:
                raise ValueError("imencode failed")

            img_base64 = base64.b64encode(img.tobytes()).decode("utf-8")
            boxes_json = json.dumps(parsed_boxes)

            return [
                TextContent(
                    type="text",
                    text="这是解析的屏幕区域GUI元素图, 图中每个解析框的左上角都紧贴着一个解析框索引，分析解析框中的元素是否是要操作的目标，找出要操作的目标框索引: ",
                ),
                ImageContent(
                    type="image",
                    data=img_base64,
                    mimeType="image/png",
                ),
                TextContent(
                    type="text",
                    text="框索引和框中心的归一化坐标对应关系为: ",
                ),
                TextContent(
                    type="text",
                    text=boxes_json,
                ),
            ]
