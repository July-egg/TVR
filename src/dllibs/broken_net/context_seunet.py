from __future__ import print_function, division
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.data
import torch
import numpy as np
from .utils import init_weights
from .utils import NormLayer, ActLayer, UpSample


# Unet Basic Convolution Block
class ConvBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int,
                 norm: str = "batch norm", act: str = "relu", init: str = "kaiming", **kwargs):
        super(ConvBlock, self).__init__()

        self.conv = nn.Sequential(
            # Note: 既然已经batch norm了，那conv的bais就没有必要了！
            nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=False),
            NormLayer(out_ch, norm=norm, **kwargs),
            ActLayer(act, inplace=True, **kwargs),

            nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=False),
            NormLayer(out_ch, norm=norm, **kwargs),
            ActLayer(act, inplace=True, **kwargs)
        )

        # initialise weights
        for m in self.children():
            init_weights(m, init_type=init)

    def forward(self, x):
        x = self.conv(x)
        return x


# Unet Basic Up Convolution Block
class UpConv(nn.Module):
    def __init__(self, in_ch: int, out_ch: int,
                 norm: str = "batch norm", act: str = "relu", init: str = "kaiming", **kwargs):
        super(UpConv, self).__init__()
        self.up = nn.Sequential(
            UpSample(upscale_factor=2, mode="bilinear", align_corners=False),
            nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=False),
            NormLayer(out_ch, norm=norm, **kwargs),
            ActLayer(inplace=True, act=act, **kwargs)
        )

        # initialise weights
        for m in self.children():
            init_weights(m, init_type=init)

    def forward(self, x):
        x = self.up(x)
        return x


# Unet SE Convolution Block
class SEConvBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int,
                 norm: str = "batch norm", act: str = "relu", init: str = "kaiming", **kwargs):
        super(SEConvBlock, self).__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=False),
            NormLayer(out_ch, norm=norm, **kwargs),
            ActLayer(act, inplace=True, **kwargs),

            nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=False),
            NormLayer(out_ch, norm=norm, **kwargs),
            ActLayer(act, inplace=True, **kwargs),

            SELayer(out_ch, reduction=16)
        )

        # initialise weights
        for m in self.children():
            init_weights(m, init_type=init)

    def forward(self, x):
        x = self.conv(x)
        return x


# Squeeze-and-Excitation Networks
# SE：Squeeze-and-Excitation 通道注意力
class SELayer(nn.Module):
    def __init__(self, channel, reduction=16):
        super(SELayer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)


class HybridPoolingModule_v3(nn.Module):
    def __init__(self, in_ch, pool_size: tuple, output_stride=16, norm="batch norm", act="relu", init="kaiming",
                 **kwargs):
        super(HybridPoolingModule_v3, self).__init__()

        if output_stride == 16:
            dilations = [1, 6, 12, 18]
        elif output_stride == 8:
            dilations = [1, 12, 24, 36]
        elif output_stride == 32:
            dilations = [1, 6, 9, 12]
        else:
            raise NotImplementedError

        int_ch = in_ch // 4

        # aspp
        self.aspp1 = nn.Sequential(
            nn.Conv2d(in_ch, int_ch, kernel_size=1, padding=0, dilation=dilations[0], bias=False),
            NormLayer(int_ch, norm)
        )

        self.aspp2 = nn.Sequential(
            nn.Conv2d(in_ch, int_ch, kernel_size=3, padding=dilations[1], dilation=dilations[1], bias=False),
            NormLayer(int_ch, norm)
        )

        self.aspp3 = nn.Sequential(
            nn.Conv2d(in_ch, int_ch, kernel_size=3, padding=dilations[2], dilation=dilations[2], bias=False),
            NormLayer(int_ch, norm)
        )

        self.aspp4 = nn.Sequential(
            nn.Conv2d(in_ch, int_ch, kernel_size=3, padding=dilations[3], dilation=dilations[3], bias=False),
            NormLayer(int_ch, norm)
        )

        self.global_avg_pool = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Conv2d(in_ch, int_ch, 1, stride=1, bias=False),
            NormLayer(int_ch, norm),
        )

        self.aspp_out = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, 1, bias=False),
            NormLayer(int_ch, norm),
            ActLayer(act, inplace=False),
            nn.Dropout(0.5)
        )

        # pyramid pooling
        self.down1 = nn.AdaptiveAvgPool2d(pool_size[0])  # (h,w) -> (pool_size[0], pool_size[0])
        self.down2 = nn.AdaptiveAvgPool2d(pool_size[1])  # (h,w) -> (pool_size[1], pool_size[1])
        self.down3 = nn.AdaptiveMaxPool2d(pool_size[0])  # (h,w) -> (pool_size[0], pool_size[0])
        self.down4 = nn.AdaptiveMaxPool2d(pool_size[1])  # (h,w) -> (pool_size[1], pool_size[1])

        # strip pooling
        self.vertical_strip_pooling = nn.AdaptiveAvgPool2d((1, None))
        self.horizon_strip_pooling = nn.AdaptiveAvgPool2d((None, 1))

        self.conv1_1 = nn.Sequential(
            nn.Conv2d(in_ch, int_ch, 1, bias=False),
            NormLayer(int_ch, norm),
            ActLayer(act, inplace=True)
        )

        self.conv1_2 = nn.Sequential(
            nn.Conv2d(in_ch, int_ch, 1, bias=False),
            NormLayer(int_ch, norm),
            ActLayer(act, inplace=True)
        )

        # self.conv1_3 = nn.Sequential(
        #     nn.Conv2d(in_ch, int_ch, 1, bias=False),
        #     NormLayer(int_ch, norm),
        #     ActLayer(act, inplace=True)
        # )

        self.conv2_0 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, 3, 1, 1, bias=False),
            NormLayer(int_ch, norm),
        )

        self.conv2_1 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, 3, 1, 1, bias=False),
            NormLayer(int_ch, norm),
        )

        self.conv2_2 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, 3, 1, 1, bias=False),
            NormLayer(int_ch, norm),
        )

        # v3 改为正确形式却效果不好?
        # self.conv2_3 = nn.Sequential(
        #     nn.Conv2d(int_ch, int_ch, 3, 1, 1, bias=False),
        #     NormLayer(int_ch, norm),
        # )
        #
        # self.conv2_4 = nn.Sequential(
        #     nn.Conv2d(int_ch, int_ch, 3, 1, 1, bias=False),
        #     NormLayer(int_ch, norm),
        # )

        self.conv2_3 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, (1, 3), 1, (0, 1), bias=False),
            NormLayer(int_ch, norm),
        )

        self.conv2_4 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, (3, 1), 1, (1, 0), bias=False),
            NormLayer(int_ch, norm),
        )

        # 和V2的不同仅在于此处：2_5 和 2_6
        self.conv2_5 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, (1, 3), 1, (0, 1), bias=False),
            NormLayer(int_ch, norm),
        )

        self.conv2_6 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, (3, 1), 1, (1, 0), bias=False),
            NormLayer(int_ch, norm),
        )

        self.conv2_7 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, 3, 1, 1, bias=False),
            NormLayer(int_ch, norm),
            ActLayer(act, inplace=True)
        )

        self.conv2_8 = nn.Sequential(
            nn.Conv2d(int_ch, int_ch, 3, 1, 1, bias=False),
            NormLayer(int_ch, norm),
            ActLayer(act, inplace=True)
        )

        self.conv3 = nn.Sequential(
            nn.Conv2d(int_ch * 3, in_ch, 1, bias=False),
            NormLayer(in_ch, norm),
        )

        self.act = ActLayer(act, inplace=True)

        # initialise weights
        for m in self.children():
            init_weights(m, init_type=init)

    def forward(self, x):
        *_, h, w = x.shape
        x1 = self.conv1_1(x)
        x2 = self.conv1_2(x)

        x2_1 = self.conv2_0(x1)
        x2_2 = F.interpolate(self.conv2_1(self.down1(x1)), (h, w), mode="bilinear", align_corners=True)
        x2_3 = F.interpolate(self.conv2_2(self.down2(x1)), (h, w), mode="bilinear", align_corners=True)
        x2_4 = F.interpolate(self.conv2_3(self.down3(x1)), (h, w), mode="bilinear", align_corners=True)
        x2_5 = F.interpolate(self.conv2_4(self.down4(x1)), (h, w), mode="bilinear", align_corners=True)

        x2_6 = F.interpolate(self.conv2_5(self.vertical_strip_pooling(x2)), (h, w), mode="bilinear", align_corners=True)
        x2_7 = F.interpolate(self.conv2_6(self.horizon_strip_pooling(x2)), (h, w), mode="bilinear", align_corners=True)

        x2_8 = self.aspp1(x)
        x2_9 = self.aspp2(x)
        x2_10 = self.aspp3(x)
        x2_11 = self.aspp4(x)
        x2_12 = F.interpolate(self.global_avg_pool(x), size=(h, w), mode='bilinear', align_corners=True)

        x1 = self.conv2_7(self.act(x2_1 + x2_2 + x2_3 + x2_4 + x2_5))
        x2 = self.conv2_8(self.act(x2_6 + x2_7))
        x3 = self.aspp_out(self.act(x2_8 + x2_9 + x2_10 + x2_11 + x2_12))

        out = self.conv3(torch.cat([x1, x2, x3], dim=1))

        return self.act(x + out)


class BottleNeckv2(nn.Module):
    def __init__(self, in_ch, out_ch, module="HPM_v4", pool_size=(20, 12), output_stride=16,
                 norm="batch norm", act="relu", init="kaiming"):
        super(BottleNeckv2, self).__init__()

        if module == "HPM_v3":
            self.rf = HybridPoolingModule_v3(out_ch, pool_size, output_stride, norm=norm, act=act, init=init)
        elif module == "none":  # 恒等映射
            self.rf = lambda _: _
        else:
            raise NotImplementedError()

        # initialise weights
        for m in self.children():
            init_weights(m, init_type=init)

    def forward(self, x):
        x = self.rf(x)
        return x


class Context_SEUNet(nn.Module):
    """
        mark: Context_SEUNet
    """

    def __init__(self, in_ch=3, out_ch=1,
                 norm="batch norm", act="relu", init="kaiming", **kwargs):
        super(Context_SEUNet, self).__init__()

        filters = [64, 128, 256, 512, 1024]

        self.down1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.down2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.down3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.down4 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.up5 = UpConv(filters[4], filters[3], norm=norm, act=act, init=init)
        self.up4 = UpConv(filters[3], filters[2], norm=norm, act=act, init=init)
        self.up3 = UpConv(filters[2], filters[1], norm=norm, act=act, init=init)
        self.up2 = UpConv(filters[1], filters[0], norm=norm, act=act, init=init)

        self.e1 = SEConvBlock(in_ch, filters[0], norm=norm, act=act, init=init)
        self.e2 = SEConvBlock(filters[0], filters[1], norm=norm, act=act, init=init)
        self.e3 = SEConvBlock(filters[1], filters[2], norm=norm, act=act, init=init)
        self.e4 = SEConvBlock(filters[2], filters[3], norm=norm, act=act, init=init)
        self.e5 = SEConvBlock(filters[3], filters[4], norm=norm, act=act, init=init)

        self.bn = BottleNeckv2(filters[3], filters[3], module="HPM_v3")

        self.d4 = ConvBlock(filters[4], filters[3], norm=norm, act=act, init=init)
        self.d3 = ConvBlock(filters[3], filters[2], norm=norm, act=act, init=init)
        self.d2 = ConvBlock(filters[2], filters[1], norm=norm, act=act, init=init)
        self.d1 = ConvBlock(filters[1], filters[0], norm=norm, act=act, init=init)

        self.out = nn.Conv2d(filters[0], out_ch, kernel_size=1, stride=1, padding=0)

        # initialise weights
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                init_weights(m, init_type=init)
            elif isinstance(m, nn.BatchNorm2d):
                init_weights(m, init_type=init)

    def forward(self, x):
        e1_out = self.e1(x)

        e2_in = self.down1(e1_out)
        e2_out = self.e2(e2_in)

        e3_in = self.down2(e2_out)
        e3_out = self.e3(e3_in)

        e4_in = self.down3(e3_out)
        e4_out = self.e4(e4_in)

        bn_in = self.down4(e4_out)
        bn_out = self.bn(bn_in)
        e5_out = self.e5(bn_out)

        d4_in = self.up5(e5_out)
        d4_in = torch.cat((e4_out, d4_in), dim=1)

        d4_out = self.d4(d4_in)

        d3_in = self.up4(d4_out)
        d3_in = torch.cat((e3_out, d3_in), dim=1)
        d3_out = self.d3(d3_in)

        d2_in = self.up3(d3_out)
        d2_in = torch.cat((e2_out, d2_in), dim=1)
        d2_out = self.d2(d2_in)

        d1_in = self.up2(d2_out)
        d1_in = torch.cat((e1_out, d1_in), dim=1)
        d1_out = self.d1(d1_in)

        out = self.out(d1_out)

        return out
