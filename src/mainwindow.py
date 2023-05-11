from os import path
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, QModelIndex
from controller import MainWindowController


from utility import config
from mainwindow_ui import Ui_MainWindow
from viewmodel import VideoHandler, ViewModel


# MainWindow 负责应用程序界面
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, controller, *args, obj=None, **kwargs) -> None:
        super(MainWindow, self).__init__(*args, **kwargs)

        self.controller: MainWindowController = controller  #

        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(path.join('assets', 'icon.ico')))

        self.videos_listmodel = QtCore.QStringListModel()
        self.videoswidget.setModel(self.videos_listmodel)

        self.viewmodel = ViewModel()  #
        self.controller.set_model(self.viewmodel)  #

        self.init()

    def init(self) -> None:
        self.infowidget.setEnabled(False)

        # menu菜单
        file = self.menubar.addMenu('文件(&F)')

        open_file = QtWidgets.QAction('打开文件', self)

        file.addAction(open_file)

        # 点击打开视频文件夹时的操作函数
        open_file.triggered.connect(self.on_open_file)

        execute = self.menubar.addMenu('检测(&D)')

        examine_one_video = QtWidgets.QAction('检测当前视频', self)
        execute.addAction(examine_one_video)
        # 检测一个视频的操作函数
        examine_one_video.triggered.connect(self.on_examine_one_video)

        examine_all_videos = QtWidgets.QAction('检测所有视频', self)
        execute.addAction(examine_all_videos)
        # 检测所有视频的操作函数
        examine_all_videos.triggered.connect(self.on_examine_all_videos)

        help = self.menubar.addMenu('帮助(&H)')

        # listview
        self.videoswidget.clicked.connect(self.on_click_video)

        self.infowidget.info_changed.connect(self.on_info_changed)

        self.viewmodel.progress_changed.connect(self.on_progresss_changed)
        self.viewmodel.video_added.connect(self.on_video_added)

    def set_message(self, message):
        self.statusBar().showMessage(message)

    def _current_handler(self) -> VideoHandler:
        # TODO: 当前未选中视频
        idx = self.videoswidget.currentIndex().row()
        handler = self.viewmodel.get(idx)
        return handler

    def add_video(self, filepath) -> None:
        self.controller.add_video(filepath)

    def activate_video(self, idx) -> None:
        if not self.infowidget.isEnabled():
            self.infowidget.setEnabled(True)

        handler = self.viewmodel.get(idx)
        self.displaywidget.set_title("视频文件：" + handler.display_name())
        self.displaywidget.set_image(handler.thumbnail())

        self.infowidget.update_details(handler.details())

    def _integrity_checking(self, idx):
        handler = self.viewmodel.get(idx)
        details = handler.details()

        if details is None:
            return False

        executor, workstation, date_time, memo = details

        return executor and workstation

    @pyqtSlot(int)
    def on_video_added(self, idx) -> None:
        handler = self.viewmodel.get(idx)
        self.videos_listmodel.insertRow(self.videos_listmodel.rowCount())
        index = self.videos_listmodel.index(self.videos_listmodel.rowCount() - 1)
        self.videos_listmodel.setData(index, handler.display_name())

        if self.videos_listmodel.rowCount() == 1:
            self.videoswidget.setCurrentIndex(self.videos_listmodel.index(0, 0))
            self.activate_video(0)

    # 根据用户填写的审计人员信息设置视频详细信息
    @pyqtSlot(tuple)
    def on_info_changed(self, info) -> None:
        idx = self.videoswidget.currentIndex().row()
        self.controller.set_video_details(idx, info)

    # 点击打开视频文件夹时的操作函数
    @pyqtSlot()
    def on_open_file(self) -> None:
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, '打开视频文件', config.get_last_video_dir(), '视频文件 (*.mp4)')

        if files:
            config.update_last_video_dir(files)

            for file in files:
                self.add_video(file)

    @pyqtSlot(QModelIndex)
    def on_click_video(self, idx: QModelIndex) -> None:
        self.activate_video(idx.row())

    # 对视频进行检测的函数
    def _examine_videos(self, dest_dir, indexes, force: bool) -> bool:
        # 获取上一次的保存地址
        config.update_last_save_dir(dest_dir)

        has_examined_video = False

        for idx in indexes:
            handler = self.viewmodel.get(idx)
            if handler.is_examined():
                has_examined_video = True

                if force:
                    self.controller.examine_video(idx, dest_dir)

            else:
                self.controller.examine_video(idx, dest_dir)

        return has_examined_video

    # 检测单个视频的函数
    @pyqtSlot()
    def on_examine_one_video(self) -> None:
        rows = self.videos_listmodel.rowCount()
        if not rows:
            return

        idx = self.videoswidget.currentIndex().row()

        if not self._integrity_checking(idx):
            QMessageBox.warning(self, '错误', '请完善视频信息后再进行质检')
            return

        dest_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, '选择保存文件夹', config.get_last_save_dir()
        )

        # 检测单个视频时，先判断是否已经质检过一次，是的话让用户进行选择
        if dest_dir:
            has_examined = self._examine_videos(dest_dir, [idx], False)
            if has_examined:
                reply = QMessageBox.question(self, '', '该视频已质检，是否再次质检？')
                if reply == QMessageBox.Yes:
                    self._examine_videos(dest_dir, [idx], True)
                else:
                    return

    @pyqtSlot()
    def on_examine_all_videos(self) -> None:
        rows = self.videos_listmodel.rowCount()
        if not rows:
            return

        for idx in range(rows):
            if not self._integrity_checking(idx):
                QMessageBox.warning(self, '错误', '请完善视频信息后再进行质检')
                self.videoswidget.setCurrentIndex(self.videos_listmodel.index(idx, 0))
                self.activate_video(idx)
                return

        dest_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, '选择保存文件夹', config.get_last_save_dir()
        )

        if dest_dir:
            self._examine_videos(dest_dir, list(range(rows)), False)

    @pyqtSlot(int, int, int)
    def on_progresss_changed(self, idx, amount, total):
        if idx == -1:
            self.set_message(f'{100}% remaining: {total}')
        else:
            self.set_message(f'{min(100 * idx / amount, 100.0):.2f}% ({idx}/{amount}) 等待中：{total}')
