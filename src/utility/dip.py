import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import math
import torch
import torchvision
import torchvision.transforms as transforms

from typing import List, Optional, Tuple, Union
from PyQt5.QtGui import QPixmap, QImage

import utility.config


def _int(val: float) -> int:
    return int(round(val))


def PIL_to_OpenCV(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def OpenCV_to_PIL(array: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(array, cv2.COLOR_BGR2RGB))


def to_PIL(image: Union[Image.Image, np.ndarray]) -> Image.Image:
    if isinstance(image, np.ndarray):
        image = OpenCV_to_PIL(image)

    return image


def to_QPixmap(image: Union[Image.Image, np.ndarray]) -> QPixmap:
    return QPixmap.fromImage(to_QImage(image))


def to_QImage(image: Union[Image.Image, np.ndarray]) -> QImage:
    if isinstance(image, Image.Image):
        image = np.asarray(image)
    else:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h, w = image_size(image)

    image = QImage(image.data, w, h, w * 3, QImage.Format_RGB888)

    return image


def tensor_to_OpenCV(tensor: torch.tensor) -> np.ndarray:
    array = tensor.numpy()
    array = np.transpose(array, (0, 2, 3, 1)) * 255
    array = array.astype(np.uint8)
    return array


def image_size(image: Union[Image.Image, np.ndarray]) -> Tuple[int, int]:
    if isinstance(image, Image.Image):
        return image.height, image.width
    else:
        h, w, d = image.shape
        return h, w


def _resize_Image(image: Image.Image, height: int, width: int, resample='cubic') -> Tuple[float, Image.Image]:
    h, w = image_size(image)
    scale_h, scale_w = height / h, width / w
    scale = min(scale_h, scale_w)
    dest_height, dest_width = _int(h * scale), _int(w * scale)

    if len(torchvision.__version__) > 11:
        inter = transforms.InterpolationMode.BICUBIC if resample == 'cubic' else transforms.InterpolationMode.BILINEAR
    else:
        inter = Image.BICUBIC if resample == 'cubic' else Image.BILINEAR

    trans = transforms.Resize((dest_height, dest_width), inter)

    res = trans(image).crop((0, 0, width, height))

    return scale, res


def resize(image: Union[Image.Image, np.ndarray], height: int, width: int, resample='cubic') -> Tuple[float, Union[Image.Image, np.ndarray]]:
    if isinstance(image, np.ndarray):
        image = OpenCV_to_PIL(image)
        scale, res = _resize_Image(image, height, width)
        return scale, PIL_to_OpenCV(res)

    return _resize_Image(image, height, width)


def rectangle(image: np.ndarray, points, color=(255, 255, 255), thickness=1) -> np.ndarray:
    l, t, r, b = [int(round(i)) for i in points]
    # l, t, r, b = round(l), round(t), round(r), round(b)
    copy = image.copy()
    res = cv2.rectangle(copy, (l, t), (r, b), color, thickness)
    return res


def square_bbox(bbox: Tuple[int, int, int, int], width: int) -> Tuple[int, int, int, int]:
    l, t, r, b = bbox
    cx, cy = (l + r) / 2, (t + b) / 2
    l, t = int(round(cx - width / 2)), int(round(cy - width / 2))
    width = int(round(width))
    return l, t, l + width, t + width

def crop_square(image: np.ndarray, bbox: Tuple[int, int, int, int], width: int) -> np.ndarray:
    l, t, r, b = square_bbox(bbox, width)
    return image[t:b, l:r]


def rectangle_and_text(image: Union[np.ndarray, Image.Image], bbox, contents, font_size=15, bgcolor=None, fgcolor=(255, 255, 255), draw_bbox=True) -> Union[np.ndarray, Image.Image]:
    def _lightness(c):
        color = list(c)
        for i, _ in enumerate(color):
            color[i] = color[i] / 255
            if color[i] <= 0.03928:
                color[i] = color[i] / 12.92
            else:
                color[i] = math.pow((color[i] + 0.055) / 1.055, 2.4)
        r, g, b = color
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _contrast(c1, c2):
        l1, l2 = _lightness(c1), _lightness(c2)
        ll, hl = min(l1, l2), max(l1, l2)
        return hl / ll

    if bgcolor is None:
        while bgcolor is None or _contrast(bgcolor, fgcolor) < 8:
            bgcolor = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

    is_array = isinstance(image, np.ndarray)

    if is_array:
        image = to_PIL(image)
    else:
        image = image.copy()

    font = ImageFont.truetype(utility.config.get_default_font(), font_size)
    imagedraw = ImageDraw.Draw(image)

    if draw_bbox:
        imagedraw.rectangle(bbox, outline=bgcolor, width=2)

    for content, pos in contents:
        origin_at, quadrant = pos[:2], pos[-1]

        bl, bt, br, bb = bbox
        if origin_at == 'lt':
            origin = bl, bt
        elif origin_at == 'rt':
            origin = br, bt
        elif origin_at == 'lb':
            origin = bl, bb
        elif origin_at == 'rb':
            origin = br, bb

        x, y = origin

        if isinstance(content, str):
            items = content.split('\n')
        else:
            items = content

        for i, item in enumerate(items[::-1]):
            item = item.strip()

            l, t, r, b = font.getbbox(item)
            w, h = l + r, t + b

            if quadrant == '3':
                l, t = x, y
            elif quadrant == '2':
                l, t = x - w, y
            elif quadrant == '0':
                l, t = x, y - h
            elif quadrant == '1':
                l, t = x - w, y - h

            t = t - i * h

            imagedraw.rectangle((l, t, l + w, t + h), fill=bgcolor, outline=bgcolor, width=2)
            imagedraw.text((l, t), item, fill=fgcolor, font=font)

    if is_array:
        return PIL_to_OpenCV(image)
    else:
        return image


def text(image: Union[np.ndarray, Image.Image], content, origin, bgcolor=None, fgcolor=(255, 255, 255)) -> Union[np.ndarray, Image.Image]:
    l, t = origin
    return rectangle_and_text(image, (l, t, l + 1, t + 1), [(content, 'lt3')], bgcolor, fgcolor, draw_bbox=False)


def stack_images(images: List[np.ndarray]) -> np.ndarray:
    return np.stack(images)


def detect_screen(image: np.ndarray) -> Optional[Tuple[float, float, float, float, float, float]]:
    # from dllibs.yolov5 import yolov5

    # yolov5.load_model()

    # scale, resized = resize(image, 640, 640)
    # box = yolov5.detect(resized)

    # if box is None:
    #     return None
    # else:
    #     box = box[0]
    #     box = box.cpu().numpy().astype(np.float64).reshape((6,))
    #     if box[-2] < box[-1]:
    #         return None
    #     box[:4] = box[:4] / scale
    #     x1, y1, x2, y2, conf, cls = box[0], box[1], box[2], box[3], box[4], box[5]
    #     return x1, y1, x2, y2, conf, cls

    return detect_screen_with_batch([image], 1, conf_thres=0.5)[0]


# 使用yolov5模型检测电视机屏幕位置，返回预测的电视机位置坐标
def detect_screen_with_batch(images: List[np.ndarray], bs: int, conf_thres=0.5) -> List[Optional[Tuple[float, float, float, float, float, float]]]:
    from dllibs.yolov5 import yolov5

    yolov5.load_model()

    scales, resized_images = [], []
    for image in images:
        scale, resized = resize(image, 640, 640)
        scales.append(scale)
        resized_images.append(resized)

    ret = []

    for i in range(0, len(scales), bs):
        bi, bj = i, i + bs
        bscales, bimages = scales[bi:bj], resized_images[bi:bj]

        arrays = stack_images(bimages)
        preds = yolov5.detect(arrays, conf_thres)
        for i, pred in enumerate(preds):
            if pred.shape[0] == 0:
                ret.append(None)
            else:
                # box = pred[0]
                _, indices = torch.max(pred, dim=0)
                max_conf_idx = indices[5]
                box = pred[max_conf_idx]
                box = box.cpu().numpy().astype(np.float64).reshape((6,))
                if int(round(box[-1])) != 0:
                    ret.append(None)
                else:
                    box[:4] = box[:4] / bscales[i]
                    x1, y1, x2, y2, conf, cls = box[0], box[1], box[2], box[3], box[4], box[5]
                    ret.append((x1, y1, x2, y2, conf, cls))

    return ret

# 使用resnet模型划分屏幕状态：荧光粉
def classify_state_with_batch(images: List[np.ndarray], bs: int):
    from dllibs.state_net import state_resnet

    state_resnet.load_model()

    resized_images = [resize(image, 224, 224, 'linear')[1] for image in images]

    ret = []

    for i in range(0, len(resized_images), bs):
        bi, bj = i, i + bs
        bimages = resized_images[bi:bj]

        arrays = stack_images(bimages)
        preds = state_resnet.classify(arrays)

        ret.extend(preds)

    return ret

# 利用碎屏检测模型判断是否碎屏（没有被调用）
def classify_broken_with_batch(images: List[np.ndarray], bs: int):
    from dllibs.broken_net import valid_resnet

    valid_resnet.load_model()

    ret = []

    resized_images = [resize(image, 224, 224, 'linear')[1] for image in images]

    for i in range(0, len(resized_images), bs):
        bi, bj = i, i + bs
        bimages = resized_images[bi:bj]

        arrays = stack_images(bimages)
        preds = valid_resnet.classify(arrays)

        ret.extend(preds)

    return ret

# 判断是否存在锥屏分离现象
def segment_cone_with_batch(images: List[np.ndarray], bs: int):
    from dllibs.seg_net import seg_net

    seg_net.load_model()

    ret = []

    resized_images = [resize(image, 256, 256, 'cubic')[1] for image in images]

    for i in range(0, len(resized_images), bs):
        bi, bj = i, i + bs
        bimages = resized_images[bi:bj]

        arrays = stack_images(bimages)
        preds = seg_net.segment(arrays)

        ret.extend(preds)

    return ret

# 判断是否存在漏氟
def segment_air_with_batch(images: List[np.ndarray], bs: int):
    from dllibs.air_net import air_net

    air_net.load_model()

    ret = []

    resized_images = [resize(image, 640, 640, 'cubic')[1] for image in images]

    for i in range(0, len(resized_images), bs):
        bi, bj = i, i + bs
        bimages = resized_images[bi:bj]

        arrays = stack_images(bimages)
        preds = air_net.segment(arrays)

        ret.extend(preds)

    return ret
