

import enum
import os
import torch
import torch.nn.functional as F
from pathlib import Path
import torch.backends.cudnn as cudnn
import torchvision.transforms as transforms

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

import utility.config
from utility.dip import OpenCV_to_PIL, tensor_to_OpenCV
from .ce_net import CE_Net
from ..helpers import select_device


class SCREEN_STATE(enum.Enum):
    FAIL = 0
    PASS = 1
    SHIELD = 2


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
    global model, device, half, weight_name

    if weight_name == utility.config.get_segment_weight():
        return

    weight_name = utility.config.get_segment_weight()

    weights = str(ROOT / 'weights' / f'{weight_name}.pth')

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    checkpoint = torch.load(weights, map_location=device)

    model = CE_Net(pretrained=False)

    # model = torch.nn.DataParallel(model).cuda()
    if torch.cuda.is_available():
        model.to(device)
    model.load_state_dict(checkpoint, False)

    model.eval()

    cudnn.benchmark = True


@torch.no_grad()
def segment(imgs):
    global model, device

    imgs = torch.stack([_compose(OpenCV_to_PIL(img)) for img in imgs], dim=0)

    imgs = imgs.to(device)

    pred = model(imgs)

    pred = torch.sigmoid(pred)
    pred = (pred > 0.5).float()

    ans = tensor_to_OpenCV(pred.cpu())

    ret = [sub_image for sub_image in ans]

    return ret
