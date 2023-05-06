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
from utility.dip import OpenCV_to_PIL
from ..resnet import resnet
from ..helpers import select_device


model = None
device = select_device()
half = None
weight_name = ''


# _compose = transforms.Compose([
#     transforms.ToTensor(),
#     transforms.transforms.Normalize(mean=[0.4154008441523197, 0.41628229198219957, 0.41887991984350065],
#                                     std=[0.13364828399314022, 0.1321730326816463, 0.13033218443040603])
# ])

_compose = transforms.Compose([
    transforms.ToTensor(),
    transforms.transforms.Normalize(mean=[0.4166430193353317, 0.4182959027833146, 0.41260498572761345],
                                    std=[0.13783641977586442, 0.1360479262305161, 0.13066597406044492])
])

# _resize_compose = transforms.Compose([
#     transforms.Resize(224),
#     transforms.ToTensor(),
#     transforms.transforms.Normalize(mean=[0.4154008441523197, 0.41628229198219957, 0.41887991984350065],
#                                     std=[0.13364828399314022, 0.1321730326816463, 0.13033218443040603])
# ])


@torch.no_grad()
def load_model():
    global model, device, half, weight_name

    if weight_name == utility.config.get_valid_weight():
        return

    weight_name = utility.config.get_valid_weight()

    weights = str(ROOT / 'weights' / f'{weight_name}.pth.tar')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    checkpoint = torch.load(weights, map_location=device)

    model = resnet.resnet([3, 4, 6, 3], num_classes=2, arch='senet', drop_layer=True, wider=False, leaky_relu=False)
    if torch.cuda.is_available():
        model = torch.nn.DataParallel(model).cuda()
    model.load_state_dict(checkpoint['state_dict'], False)

    model.eval()

    cudnn.benchmark = True


@torch.no_grad()
def classify(imgs):
    global model, device

    imgs = torch.stack([_compose(OpenCV_to_PIL(img)) for img in imgs], dim=0)

    pred = model(imgs)

    pred = F.softmax(pred, dim=1)

    pred = [p[0].item() for p in pred]

    return pred


@torch.no_grad()
def classify_one_image(img):
    global model, device

    img = OpenCV_to_PIL(img)
    imgs = torch.stack([_compose(img)], dim=0)

    pred = model(imgs)

    pred = F.softmax(pred, dim=1)

    pred = [p[0].item() for p in pred]

    return pred
