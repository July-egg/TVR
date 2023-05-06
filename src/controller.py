import multiprocessing
from pathlib import Path
import queue
from threading import Thread
from typing import Optional
import datetime

from utility.arbiter import Arbiter
from utility.serializer import ResultSerializer
from viewmodel import ViewModel


# 视频检测线程
def _examine_videos(videos_queue, summary_queue, progress_queue):
    while True:
        finished, video_path, fps, details, dest_dir, use_detectors = videos_queue.get()

        if finished:
            summary_queue.put((True, None, None, None, None, None))
            break

        name = Path(video_path).stem
        output_dir = Path(dest_dir) / name
        output_dir.mkdir(exist_ok=True)

        arbiter = Arbiter(0.8, str(output_dir), use_detectors)
        results = arbiter.arbitrate(video_path, progress_queue=progress_queue)

        summary_queue.put((finished, video_path, fps, details, dest_dir, results))

        del arbiter
        del results


# 保存检测结果线程
def _save_results(summary_queue):
    while True:
        finished, video_path, fps, details, dest_dir, results = summary_queue.get()

        if finished:
            break

        executor, workstation, date_time, memo = details

        name = Path(video_path).stem
        save_dir = Path(dest_dir) / name
        save_dir.mkdir(exist_ok=True)

        dic = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        parts = date_time.split(' ')
        year, month, day, t = parts[3], dic[parts[1]], parts[2], parts[4]
        h, m, s = t.split(':')
        year, month, day, h, m, s = [int(x) for x in [year, month, day, h, m, s]]
        date_time = datetime.datetime(year, month, day, h, m, s)

        serializer = ResultSerializer()
        serializer.serialize(save_dir, video_path, fps, executor, workstation, date_time, memo, results)


# 实时监测线程数量，当前无运行线程时结束
def _progress_notifier(progress_queue, controller):
    while True:
        i, amount = progress_queue.get()

        if i is None:
            break

        controller.notify_progress(i, amount)

# 添加视频线程
def _add_video(video_path_queue: queue.Queue, controller):
    while True:
        video_path = video_path_queue.get()

        if video_path is None:
            break
        controller._add_video(video_path)


# MainWindowController 负责实现检测功能
class MainWindowController:
    def __init__(self, use_detectors):
        self.use_detectors = use_detectors

        self.videos_queue = multiprocessing.Queue()
        self.summary_queue = multiprocessing.Queue()
        self.progress_queue = multiprocessing.Queue()
        self.video_path_queue = queue.Queue()

        self.examine_process = multiprocessing.Process(
            target=_examine_videos, args=(self.videos_queue, self.summary_queue, self.progress_queue)
        )

        self.io_thread = Thread(
            target=_save_results, args=(self.summary_queue,)
        )

        self.progress_thread = Thread(
            target=_progress_notifier, args=(self.progress_queue, self)
        )

        self.add_video_thread = Thread(
            target=_add_video, args=(self.video_path_queue, self)
        )

        self.add_video_thread.start()
        self.examine_process.start()
        self.io_thread.start()

        self.model: Optional[ViewModel] = None

    def set_model(self, model):
        self.model = model
        self.progress_thread.start()

    def _add_video(self, video_path):
        print('self.model._add_video 运行中....')
        self.model.add(video_path)
        print('len(self.model._video_handlers): ', len(self.model._video_handlers))


    def add_video(self, video_path):
        self.video_path_queue.put(video_path)

    def set_video_details(self, idx, details):
        print('运行set_video_details, idx: ', idx)
        print('model:', self.model)
        print('model._video_handlers:', self.model._video_handlers)
        handeler = self.model.get(idx)
        handeler.set_details(details)

    def notify_progress(self, i, amount):
        if self.model is not None:
            self.model.set_progress(i, amount, self.videos_queue.qsize())

    def examine_video(self, idx, dest_dir):
        handler = self.model.get(idx)
        handler.set_examined(True)
        # 在视频检测线程中添加新视频
        self.videos_queue.put((False, handler.video_path(), handler.fps(), handler.details(), dest_dir, self.use_detectors))

    def exit(self, kill_all=False):
        if kill_all:
            self.examine_process.terminate()
            self.summary_queue.put((True, None, None, None, None, None))
        else:
            self.videos_queue.put((True, None, None, None, None, None))
            self.examine_process.join()

        self.progress_queue.put((None, None))
        self.video_path_queue.put(None)

        self.io_thread.join()
        self.progress_thread.join()
        self.add_video_thread.join()
