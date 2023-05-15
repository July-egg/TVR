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

from mmyolo.registry import VISUALIZERS
from mmyolo.utils import switch_to_deploy
from mmyolo.utils.labelme_utils import LabelmeFormat
from mmyolo.utils.misc import get_file_list, show_data_classes


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative
cfg_path = 'yolov5_s-v61_syncbn_1xb16-300e_fog.py'

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


_compose = transforms.Compose([
    transforms.ToTensor(),
    transforms.transforms.Normalize(mean=[0.4235219742122354, 0.4236387289952207, 0.4216347693022993],
                                    std=[0.140677661676244, 0.13928682011772153, 0.13288340206878646])
])


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

    model.cfg.test_dataloader.dataset.pipeline[
        0].type = 'mmdet.LoadImageFromNDArray'
    test_pipeline = Compose(model.cfg.test_dataloader.dataset.pipeline)

    imgs = imgs.transpose((0, 3, 1, 2))[:, ::-1]
    imgs = np.ascontiguousarray(imgs)

    im = torch.from_numpy(imgs).to(device)
    im = im.half() if half else im.float()

    im /= 255

    pred = inference_detector(model, imgs, test_pipeline=test_pipeline)

    pred_instances = pred.pred_instances[
        pred.pred_instances.scores > conf_thres]

    ret = [p.cpu() for p in pred_instances]

    return ret
