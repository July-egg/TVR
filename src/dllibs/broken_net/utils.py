from collections import OrderedDict
from torch import nn
import numpy as np
import torch
import os

__all__ = ['NormLayer', 'ActLayer', 'ConvLayer', 'UpSample', 'init_weights']


# ----------------- layers --------------------
# norm layer
class NormLayer(nn.Module):
    def __init__(self, num_features: int, norm: str = "instance norm", **kwargs):
        super(NormLayer, self).__init__()
        if norm == "instance norm":   # affine=False 无参数
            self.norm = nn.InstanceNorm2d(num_features, affine=False, track_running_stats=False)
        elif norm == "batch norm":  # affine=True 有参数, track_running_stats=True 全局mean和var
            self.norm = nn.BatchNorm2d(num_features, affine=True, track_running_stats=True)
        elif norm == "group norm":
            n_g = kwargs.get("num_groups", 1)
            self.norm = nn.GroupNorm(n_g, num_features, affine=True)
        else:
            raise NotImplementedError("No such norm: %s" % norm)

    def forward(self, x):
        return self.norm(x)


# activate layer
class ActLayer(nn.Module):
    def __init__(self, act="leaky relu", inplace=True, **kwargs):
        super(ActLayer, self).__init__()

        if act == "leaky relu":
            n_s = kwargs.get("negative_slope", 1e-2)
            self.act = nn.LeakyReLU(n_s, inplace)

        elif act == "relu":
            self.act = nn.ReLU(inplace)

        elif act == "prelu":
            n_p = kwargs.get("num_parameters", 1)
            init = kwargs.get("init", 0.25)
            self.act = nn.PReLU(n_p, init)

        elif act == "rrelu":
            lower = kwargs.get('lower', 1.0 / 8)
            upper = kwargs.get('upper', 1.0 / 3)
            self.act = nn.RReLU(lower, upper, inplace)

        elif act == "elu":
            alpha = kwargs.get('alpha', 1.0)
            self.act = nn.ELU(alpha, inplace)

        elif act == "celu":
            alpha = kwargs.get('alpha', 1.0)
            self.act = nn.CELU(alpha, inplace)

        elif act == "selu":
            self.act = nn.SELU(inplace)

        elif act == "glu":
            dim = kwargs.get('dim', -1)
            self.act = nn.GLU(dim)

        elif act == "sigmoid":
            self.act = nn.Sigmoid()

        elif act == "log sigmoid":
            self.act = nn.LogSigmoid()

        elif act == "tanh":
            self.act = nn.Tanh()

        elif act == "hard tanh":
            min_val = kwargs.get('min_val', -1.0)
            max_val = kwargs.get('max_val', 1.0)
            self.act = nn.Hardtanh(min_val, max_val, inplace)

        elif act == "softplus":
            beta = kwargs.get('beta', 1.0)
            threshold = kwargs.get('threshold', 20)
            self.act = nn.Softplus(beta, threshold)

        elif act == "softshrink":
            lambd = kwargs.get('lambda', 0.5)
            self.act = nn.Softshrink(lambd)

        elif act == "softsign":
            self.act = nn.Softsign()

        elif act == "softmax":
            self.act = nn.Softmax()

        else:
            raise NotImplementedError("No such activate function: %s" % act)

    def forward(self, x):
        return self.act(x)


# stack conv layer
class ConvLayer(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, kernel_size: [int, tuple], stride: [int, tuple] = 1,
                 padding: [int, tuple] = 0, dilation: [int, tuple] = 1, blocks: int = 1,
                 norm: str = "batch norm", act: str = "relu", init: str = "kaiming"):
        super(ConvLayer, self).__init__()

        self.seq = nn.Sequential(OrderedDict([
            ('conv1', nn.Conv2d(in_ch, out_ch, kernel_size, stride, padding, dilation, bias=True)),
            ('norm1', NormLayer(out_ch, norm)),
            ('act1', ActLayer(act, inplace=True))
        ]))

        for _ in range(2, blocks+1):
            self.seq.add_module("conv%d" % _, nn.Conv2d(out_ch, out_ch, kernel_size, stride, padding, dilation, bias=True))
            self.seq.add_module("norm%d" % _, NormLayer(out_ch, norm))
            self.seq.add_module("act%d" % _, ActLayer(act, inplace=True))

        # init wights
        for m in self.children():
            init_weights(m, init_type=init)

    def forward(self, x):
        return self.seq(x)


# up-sample layer
class UpSample(nn.Module):
    def __init__(self, in_ch: int = None, out_ch: int = None, upscale_factor: int = 2, mode: str = "linear", **kwargs):
        super(UpSample, self).__init__()
        if mode == "pixel shuffle":
            self.up = nn.PixelShuffle(upscale_factor)
        elif mode == "nearest" or mode == "linear" or mode == "bilinear" or mode == "trilinear":
            self.up = nn.Upsample(scale_factor=upscale_factor, mode=mode, **kwargs)
        elif mode == "deconvolution":
            self.up = nn.ConvTranspose2d(in_ch, out_ch, **kwargs)

    def forward(self, x):
        return self.up(x)


# ----------------- 权重初始化 --------------------
def weights_init_normal(m):  # normal 权重初始化
    classname = m.__class__.__name__
    # print(classname)
    if classname.find('Conv') != -1 or classname.find('Linear') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0.0)
    elif classname.find('InstanceNorm') != -1:
        pass  # IN 默认无可学习参数
    else:
        pass


def weights_init_xavier(m):   # xavier 权重初始化
    classname = m.__class__.__name__
    # print(classname)
    if classname.find('Conv') != -1 or classname.find('Linear') != -1:
        nn.init.xavier_normal_(m.weight.data, gain=1)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0.0)
    elif classname.find('InstanceNorm') != -1:
        pass    # IN 默认无可学习参数
    else:
        pass


def weights_init_kaiming(m):   # kaiming 权重初始化
    classname = m.__class__.__name__
    # print(classname)
    if classname.find('Conv') != -1 or classname.find('Linear') != -1:
        nn.init.kaiming_normal_(m.weight.data, a=0, mode='fan_in')
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0.0)
    elif classname.find('InstanceNorm') != -1:
        pass  # IN 默认无可学习参数
    else:
        pass


def weights_init_orthogonal(m):     #orthogonal 权重初始化
    classname = m.__class__.__name__
    # print(classname)
    if classname.find('Conv') != -1 or classname.find('Linear') != -1:
        nn.init.orthogonal_(m.weight.data, gain=1)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0.0)
    elif classname.find('InstanceNorm') != -1:
        pass  # IN 默认无可学习参数
    else:
        pass


def init_weights(net, init_type='normal'):
    if init_type == 'normal':
        net.apply(weights_init_normal)
    elif init_type == 'xavier':
        net.apply(weights_init_xavier)
    elif init_type == 'kaiming':
        net.apply(weights_init_kaiming)
    elif init_type == 'orthogonal':
        net.apply(weights_init_orthogonal)
    else:
        raise NotImplementedError('initialization method [%s] is not implemented' % init_type)
