from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QSizePolicy
from PyQt5 import QtGui
from PyQt5.QtGui import QPalette, QColor, QPixmap

import numpy as np

from utility import dip


class ImageView(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.pixmap: QPixmap = None

    def setPixmap(self, pixmap) -> None:
        self.pixmap = pixmap
        self.update()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        if self.pixmap is not None:
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            rect = self.rect()
            if rect.width() / rect.height() > self.pixmap.width() / self.pixmap.height():
                scale = rect.height() / self.pixmap.height()
                width = round(scale * self.pixmap.width())
                left = round((rect.width() - width) / 2)
                painter.drawPixmap(left, 0, width, rect.height(), self.pixmap)
            else:
                scale = rect.width() / self.pixmap.width()
                height = round(scale * self.pixmap.height())
                top = round((rect.height() - height) / 2)
                painter.drawPixmap(0, top, rect.width(), height, self.pixmap)

        return super().paintEvent(a0)


class ImageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.title_widget = QtWidgets.QLabel()
        self.layout.addWidget(self.title_widget)

        self.view_widget = ImageView()
        # self.view_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # self.view_widget.setScaledContents(True)
        self.layout.addWidget(self.view_widget)

        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 1)

    def set_title(self, title: str) -> None:
        self.title_widget.setText(title)

    def set_image(self, image: np.ndarray) -> None:
        self.view_widget.setPixmap(dip.to_QPixmap(image))
