

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
from .context_seunet import Context_SEUNet
from ..helpers import select_device

model = None
device = select_device()
half = None
weight_name = ''


_compose = transforms.Compose([
    transforms.ToTensor(),
    transforms.transforms.Normalize(mean=[0.35740975, 0.35927135, 0.36786193],
                                    std=[0.169528, 0.16850878, 0.17494833])
])


@torch.no_grad()
def load_model():
    global model, device, half, weight_name

    if weight_name == utility.config.get_broken_weight():
        return

    weight_name = utility.config.get_broken_weight()

    weights = str(ROOT / 'weights' / f'{weight_name}.pth')

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    checkpoint = torch.load(weights, map_location=device)

    model = Context_SEUNet(pretrained=False)

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
