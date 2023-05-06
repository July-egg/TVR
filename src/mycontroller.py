import multiprocessing
from pathlib import Path
import queue
from threading import Thread
from typing import Optional
import datetime

from utility.arbiter import Arbiter
from utility.serializer import ResultSerializer
from myviewmodel import ViewModel


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


# MainWindowController 负责实现检测功能
class MainWindowController:
    def __init__(self, use_detectors):
        self.use_detectors = use_detectors

        self.videos_queue = multiprocessing.Queue()
        self.summary_queue = multiprocessing.Queue()
        self.progress_queue = multiprocessing.Queue()
        self.video_path_queue = queue.Queue()

        self.io_thread = Thread(
            target=_save_results, args=(self.summary_queue,)
        )

        self.progress_thread = Thread(
            target=_progress_notifier, args=(self.progress_queue, self)
        )

        self.io_thread.start()
        self.model: Optional[ViewModel] = None

    def set_model(self, model):
        self.model = model
        self.progress_thread.start()

    def add_video(self, video_path):
        self.video_path_queue.put(video_path)
        self.model.add(video_path)

    def set_video_details(self, idx, details):
        print('运行set_video_details, idx: ', idx)
        # print('model:', self.model)
        self.model.get(idx).set_details(details)

    def notify_progress(self, i, amount):
        if self.model is not None:
            self.model.set_progress(i, amount, self.videos_queue.qsize())

    def examine_video(self, idx, dest_dir, type):
        handler = self.model.get(idx)
        handler.set_examined(True)

        finished, video_path, fps, details, dest_dir, use_detectors = (False, handler.video_path(), handler.fps(), handler.details(), dest_dir, self.use_detectors)
        self.video_path_queue.get()

        if finished:
            self.summary_queue.put((True, None, None, None, None, None))
            return

        name = Path(video_path).stem
        output_dir = Path(dest_dir) / name
        output_dir.mkdir(exist_ok=True)

        arbiter = Arbiter(0.8, str(output_dir), use_detectors)
        results = arbiter.arbitrate(video_path, type=type, progress_queue=self.progress_queue)

        self.summary_queue.put((finished, video_path, fps, details, dest_dir, results))

        del arbiter
        del results

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
