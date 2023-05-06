# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Run inference on images, videos, directories, streams, etc.

Usage - sources:
    $ python path/to/yolov7.py --weights yolov5s.pt --source 0              # webcam
                                                             img.jpg        # image
                                                             vid.mp4        # video
                                                             path/          # directory
                                                             path/*.jpg     # glob
                                                             'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                             'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python path/to/yolov7.py --weights yolov5s.pt                 # PyTorch
                                         yolov5s.torchscript        # TorchScript
                                         yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                         yolov5s.xml                # OpenVINO
                                         yolov5s.engine             # TensorRT
                                         yolov5s.mlmodel            # CoreML (MacOS-only)
                                         yolov5s_saved_model        # TensorFlow SavedModel
                                         yolov5s.pb                 # TensorFlow GraphDef
                                         yolov5s.tflite             # TensorFlow Lite
                                         yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import torch
import torch.backends.cudnn as cudnn
import numpy as np

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.datasets import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync

import utility.config


yolov5 = None
device = select_device('')
half = None
weight_name = ''

@torch.no_grad()
def load_model():
    global yolov5, device, half, weight_name

    if weight_name ==  utility.config.get_detection_weight():
        return

    weight_name = utility.config.get_detection_weight()

    weights = str(ROOT / 'weights' / f'{weight_name}.pt')

    yolov5 = DetectMultiBackend(weights, device=device, dnn=False, data=None)

    half = (yolov5.pt or yolov5.jit or yolov5.onnx or yolov5.engine) and device.type != 'cpu'
    if yolov5.pt or yolov5.jit:
        yolov5.model.half() if half else yolov5.model.float()

    cudnn.benchmark = True

    bs = utility.config.get_batch_info()['detection']

    yolov5.eval()

    yolov5.warmup(imgsz=(1 if yolov5.pt else bs, 3, 640, 640), half=half)


@torch.no_grad()
def detect(imgs, conf_thres=0.5) -> torch.Tensor:
    global yolov5, device, half

    imgs = imgs.transpose((0, 3, 1, 2))[:, ::-1]
    imgs = np.ascontiguousarray(imgs)

    im = torch.from_numpy(imgs).to(device)
    im = im.half() if half else im.float()

    im /= 255

    pred = yolov5(im, augment=False, visualize=False)

    pred = non_max_suppression(pred,
                               conf_thres=conf_thres,
                               iou_thres=0.45,
                               classes=None,
                               agnostic=False,
                               max_det=1000)

    ret = [p.cpu() for p in pred]

    torch.cuda.empty_cache()

    return ret

    ret = []
    for p in enumerate(pred):
        if p.shape[0] > 0:
            ret.append(p[0])
        else:
            ret.append(None)

    return ret

    return pred

    det = pred[0]

    if len(det):
        det[:, :4] = det[:, :4].round()
        return det
    else:
        return None

    # for det in pred:
    #     if len(det):
    #         det[:, :4] = det[:, :4].round()

    #         print(det[:, :6])
