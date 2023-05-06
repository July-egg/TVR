import argparse
import sys
from PyQt5 import QtWidgets

from mainwindow import MainWindow
from controller import MainWindowController

from utility import config


parser = argparse.ArgumentParser()
parser.add_argument('--use-detectors', action='store_true')
parser.add_argument('--kill-all-when-exit', action='store_true')


if __name__ == '__main__':
    # 创建QApplication类的实例
    app = QtWidgets.QApplication(sys.argv)

    font = app.font()
    font.setPointSize(15)
    app.setFont(font)

    args = parser.parse_args()

    # 创建controller控制类
    controller = MainWindowController(args.use_detectors)

    # 创建一个窗口并显示
    window = MainWindow(controller)
    window.show()

    ret = app.exec_()

    controller.exit(kill_all=args.kill_all_when_exit)

    config.save_config()

    # 进入程序的主循环，并通过exit函数确保主循环安全结束(该释放资源的一定要释放)
    sys.exit(ret)
