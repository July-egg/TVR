import os
from argparse import ArgumentParser
from pathlib import Path
import enum
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
cfg_path = 'dllibs/air_net/yolov5_s-v61_syncbn_1xb16-300e_fog.py'

import utility.config
from utility.dip import OpenCV_to_PIL, tensor_to_OpenCV
from ..helpers import select_device


class AIR_STATE(enum.Enum):
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
    if weight_name == utility.config.get_air_weight():
        return
    weight_name = utility.config.get_air_weight()
    weights = str(ROOT / 'weights' / f'{weight_name}.pth')

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # checkpoint = torch.load(weights, map_location=device)
    checkpoint = weights

    model = init_detector(config, checkpoint, device=device, cfg_options={})

    if torch.cuda.is_available():
        model.to(device)

    model.eval()

    cudnn.benchmark = True


@torch.no_grad()
def segment(imgs):
    global model, device

    imgs = torch.stack([_compose(OpenCV_to_PIL(img)) for img in imgs], dim=0)

    imgs = imgs.to(device)

    # pred = [inference_detector(model, img) for img in imgs]
    test_pipeline = Compose(model.cfg.test_dataloader.dataset.pipeline)
    pred = inference_detector(model, imgs)

    pred = torch.sigmoid(pred)
    pred = (pred > 0.5).float()

    ans = tensor_to_OpenCV(pred.cpu())

    ret = [sub_image for sub_image in ans]

    return ret
