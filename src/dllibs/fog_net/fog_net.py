import os
from argparse import ArgumentParser
from pathlib import Path
import enum
import numpy as np
import torch
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
import torchvision.transforms as transforms

import mmcv
from mmcv.transforms import Compose
from mmdet.apis import inference_detector, init_detector
from mmengine.config import Config, ConfigDict
from mmengine.logging import print_log
from mmengine.utils import ProgressBar, path


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative
# print(ROOT)
cfg_path = os.path.join(ROOT, 'yolov5_s-v61_syncbn_1xb16-300e_fog.py')

import utility.config
from utility.dip import OpenCV_to_PIL, tensor_to_OpenCV
from ..helpers import select_device


class FOG_STATE(enum.Enum):
    EXIST = 0
    NONE = 1


model = None
device = select_device()
half = None
weight_name = ''


@torch.no_grad()
def load_model():
    global model, device, half, weight_name, cfg_path

    # 获取配置文件信息
    config = Config.fromfile(cfg_path)
    if 'init_cfg' in config.model.backbone:
        config.model.backbone.init_cfg = None

    if weight_name == utility.config.get_fog_weight():
        return
    weight_name = utility.config.get_fog_weight()
    checkpoint = str(ROOT / 'weights' / f'{weight_name}.pth')

    device_fog = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = init_detector(config, checkpoint, device=device_fog, cfg_options={})


@torch.no_grad()
def detect(imgs, conf_thres=0.5):  # conf_thres设置0.5还是0.3？
    global model, device

    preds = inference_detector(model, imgs)
    ret = []
    for pred in preds:
        pred_instance = pred.pred_instances[
            pred.pred_instances.scores > conf_thres]
        print(pred_instance.cpu().numpy())
        ret.append(pred_instance.cpu().numpy())

    return ret
