from utility.video import Video
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

# 保存单个视频信息
class VideoHandler:
    def __init__(self, video_path: str) -> None:
        self._video_path = video_path

        self._thumbnail = None
        self._w = None
        self._h = None
        self._fps = None
        self._display_name = Path(self._video_path).stem

        with Video(self._video_path) as v:
            self._thumbnail = v.read()

            self._w = v.frame_width()
            self._h = v.frame_height()
            self._fps = v.computed_fps()

        assert self._thumbnail is not None

        self._details = None
        self._is_examined = False

    def display_name(self) -> str:
        return self._display_name

    def video_path(self) -> str:
        return self._video_path

    def fps(self) -> float:
        return self._fps

    def thumbnail(self):
        return self._thumbnail

    def details(self):
        return self._details

    def set_details(self, details) -> None:
        self._details = details

    def is_examined(self) -> bool:
        return self._is_examined

    def set_examined(self, val) -> None:
        self._is_examined = val


# ViewModel 保存视频路径以及填写的视频信息
class ViewModel(QObject):
    progress_changed = pyqtSignal(int, int, int)
    video_added = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()

        self._video_handlers = []

    def get(self, idx: int) -> VideoHandler:
        return self._video_handlers[idx]

    def add(self, video_path: str, idx: int = -1):
        if idx < 0:
            self._video_handlers.append(VideoHandler(video_path))
        else:
            handler = VideoHandler(video_path)
            self._video_handlers.insert(idx, handler)

        self.video_added.emit(idx)

    def set_progress(self, idx, amount, total):
        self.progress_changed.emit(idx, amount, total)
