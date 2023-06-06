from datetime import datetime
import enum
from typing import Callable, List, Optional, Tuple, Any
import numpy as np

from .tools import index_of_first, index_of_last, max_seq_len, max_seq_len_with_torlenance
from .dip import (
    detect_screen_with_batch,
    classify_broken_with_batch,
    classify_state_with_batch,
    crop_square,
    segment_cone_with_batch,
    detect_fog_with_batch
)

from .video import Video
from .config import get_batch_info

# 每秒优先检测帧数
SCREEN_DETECTION_FREQUENCY = 3
FOG_DETECTION_FREQUENCY = 6
# 每秒检测帧数放大率，与 SCREEN_DETECTION_FREQUENCY 的差值为待检测帧数
DIAGNOSIS_MAGNIFICATION_RATIO = 2
# 目标检测长尾时间
SCREEN_DETECTION_TAIL_TIME = 6
FOG_DETECTION_TAIL_TIME = 6
# 关键工序最短时长
SCREEN_DETECTION_MINIMUM_DURATION = 6
FOG_DETECTION_MINIMUM_DURATION = 2
# Section 临界帧数量，超过该帧数则先返回部分 Section
SCREEN_DETECTION_CACHE_MAXIMUM = 30 * SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO
FOG_DETECTION_CACHE_MAXIMUM = 30 * FOG_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO

assert SCREEN_DETECTION_CACHE_MAXIMUM > SCREEN_DETECTION_MINIMUM_DURATION * SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO
assert FOG_DETECTION_CACHE_MAXIMUM > FOG_DETECTION_MINIMUM_DURATION * FOG_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO

SCREEN_DETECTION_BATCH_SIZE = get_batch_info()['detection']
PHOSPHOR_DETECTION_BATCH_SIZE = get_batch_info()['state_test']
BROKEN_DETECTION_BATCH_SIZE = get_batch_info()['broken_test']
CONE_DETECTION_BATCH_SIZE = get_batch_info()['segmentation']
FOG_DETECTION_BATCH_SIZE = get_batch_info()['detection']


class FRAME_TAG(enum.Enum):
    IGNORED = 0
    SHOULD_DETECT = 1
    DETECT_LATER = 2


# 获取视频帧并返回
class FrameFilter:
    def __init__(self, video_path: str, set_end_flag: bool = False, video_type='tv',
                 detector: Callable[[FRAME_TAG, int, np.ndarray, float], None] = None) -> None:
        self.video_path = video_path
        self.video = Video(self.video_path)
        self.fps = self.video.fps()
        self.computed_fps = self.video.computed_fps()

        computed_fps = self.computed_fps
        if video_type == 'tv':
            self.detect_gap_frames = round(computed_fps / SCREEN_DETECTION_FREQUENCY)
        else:
            self.detect_gap_frames = round(computed_fps / FOG_DETECTION_FREQUENCY)
        self.undetect_gap_frames = round(self.detect_gap_frames / DIAGNOSIS_MAGNIFICATION_RATIO)

        self.set_end_flag = set_end_flag

        self.idx = -1

        self.detector = detector

    def close(self) -> None:
        self.video.close()

    def video_total_time(self) -> float:
        return self.video.frame_count() / self.computed_fps

    def __len__(self) -> int:
        return (self.video.frame_count() // self.detect_gap_frames) * DIAGNOSIS_MAGNIFICATION_RATIO

    def __iter__(self):
        while True:
            reminder = self.idx % self.detect_gap_frames

            if self.detector is not None:
                start_time = datetime.now()

            self.idx += 1
            msec = self.video.pos_mesc()
            frame = self.video.read()

            if self.detector is not None:
                frame_read_time = (datetime.now() - start_time).total_seconds()

            if frame is None:
                if self.set_end_flag:
                    yield None, -1, None, None

                return

            if reminder == 0:

                if self.detector is not None:
                    self.detector(FRAME_TAG.SHOULD_DETECT, self.idx, frame, frame_read_time)

                yield FRAME_TAG.SHOULD_DETECT, self.idx, msec, frame

            elif (reminder % self.undetect_gap_frames == 0 and
                  reminder // self.undetect_gap_frames < DIAGNOSIS_MAGNIFICATION_RATIO):

                if self.detector is not None:
                    self.detector(FRAME_TAG.DETECT_LATER, self.idx, frame, frame_read_time)

                yield FRAME_TAG.DETECT_LATER, self.idx, msec, frame

            else:

                if self.detector is not None:
                    self.detector(FRAME_TAG.IGNORED, self.idx, frame, frame_read_time)


# 将视频按帧划分
class Sectionalizer:
    class State(enum.Enum):
        IN_SECTION = 1
        OUT_OF_SECTION = 2

    def __init__(self, conf_thres: float,
                 detector: Callable[[bool, int, int, np.ndarray, Optional[Tuple]], None] = None) -> None:
        self.state = self.State.OUT_OF_SECTION

        self.conf_thres = conf_thres

        self.immediate_frames: List[np.ndarray] = []
        self.deferred_frames: List[np.ndarray] = []

        self.ready = False
        self.section_info = ([], [], [])
        self.section_detect_flags = []
        self.section = None

        self.section_idx = 0
        self.detector = detector

        self.is_unfinished = False

    def is_ready(self) -> bool:
        return self.ready

    def retrieve_section(self):
        ret = self.section
        self.ready = False
        self.section = None
        return not self.is_unfinished, ret

    def add_frame(self, tag: FRAME_TAG, idx: int, msec: float, frame: np.ndarray) -> None:
        if idx < 0:
            self._finish()
            return

        if tag == FRAME_TAG.DETECT_LATER:
            self.deferred_frames.append((idx, msec, frame))
        # 如果当前帧需要被检测，加入序列
        elif tag == FRAME_TAG.SHOULD_DETECT:
            self.immediate_frames.append((idx, msec, frame))

            # 如果当前批次数量已够，调用yolov5依次检测每一帧的屏面玻璃位置----------------->
            if len(self.immediate_frames) == SCREEN_DETECTION_BATCH_SIZE:
                ans = detect_screen_with_batch([
                    frame for _, _, frame in self.immediate_frames
                ], SCREEN_DETECTION_BATCH_SIZE, self.conf_thres)

                # 如果新开始检测一个批次帧 且 检测到了屏面玻璃
                if self.state == self.State.OUT_OF_SECTION:
                    if self._found_screen(ans):
                        self.state = self.State.IN_SECTION

                        self.section_info[0].extend(self.immediate_frames)
                        self.section_info[1].extend(self.deferred_frames)
                        self.section_info[2].extend(ans)
                        self.section_detect_flags.extend(None if frame_res is None else 1 for frame_res in ans)

                elif self.state == self.State.IN_SECTION:
                    self.section_info[0].extend(self.immediate_frames)
                    self.section_info[1].extend(self.deferred_frames)
                    self.section_info[2].extend(ans)
                    self.section_detect_flags.extend(None if frame_res is None else 1 for frame_res in ans)

                    if self._section_is_over():
                        self.state = self.State.OUT_OF_SECTION

                        self.parse(is_over=True)

                        self.immediate_frames.clear()
                        self.deferred_frames.clear()

                        return

                self.immediate_frames.clear()
                self.deferred_frames.clear()

                # 判断当前缓存是否已满
                if len(self.section_info[0]) + len(self.section_info[1]) >= SCREEN_DETECTION_CACHE_MAXIMUM:
                    self.parse(is_over=False)

    def add_frame_fog(self, tag: FRAME_TAG, idx: int, msec: float, frame: np.ndarray) -> None:
        if idx < 0:
            self._finish_fog()
            return

        if tag == FRAME_TAG.DETECT_LATER:
            self.deferred_frames.append((idx, msec, frame))
        # 如果当前帧需要被检测，加入序列
        elif tag == FRAME_TAG.SHOULD_DETECT:
            self.immediate_frames.append((idx, msec, frame))

            # 如果当前批次数量已够，调用yolov5依次检测每一帧的屏面玻璃位置----------------->
            if len(self.immediate_frames) == FOG_DETECTION_BATCH_SIZE:
                ans = detect_fog_with_batch([
                    frame for _, _, frame in self.immediate_frames
                ], FOG_DETECTION_BATCH_SIZE, conf_thres=0.3)

                # 如果新开始检测一个批次帧 且 检测到了fog
                if self.state == self.State.OUT_OF_SECTION:
                    if self._found_screen(ans):
                        self.state = self.State.IN_SECTION

                        self.section_info[0].extend(self.immediate_frames)
                        self.section_info[1].extend(self.deferred_frames)
                        self.section_info[2].extend(ans)
                        self.section_detect_flags.extend(None if frame_res is None else 1 for frame_res in ans)

                elif self.state == self.State.IN_SECTION:
                    self.section_info[0].extend(self.immediate_frames)
                    self.section_info[1].extend(self.deferred_frames)
                    self.section_info[2].extend(ans)
                    self.section_detect_flags.extend(None if frame_res is None else 1 for frame_res in ans)

                    if self._section_is_over_fog():
                        self.state = self.State.OUT_OF_SECTION

                        self.parse_fog(is_over=True)

                        self.immediate_frames.clear()
                        self.deferred_frames.clear()

                        return

                self.immediate_frames.clear()
                self.deferred_frames.clear()

                # 判断当前缓存是否已满
                if len(self.section_info[0]) + len(self.section_info[1]) >= FOG_DETECTION_CACHE_MAXIMUM:
                    self.parse_fog(is_over=False)

    def _finish(self) -> None:
        # 对最后一个需要检测的帧重复add_frame中的操作
        ans = detect_screen_with_batch([
            frame for _, _, frame in self.immediate_frames
        ], SCREEN_DETECTION_BATCH_SIZE, self.conf_thres)

        if self.state == self.State.IN_SECTION or self._found_screen(ans):
            self.section_info[0].extend(self.immediate_frames)
            self.section_info[1].extend(self.deferred_frames)
            self.section_info[2].extend(ans)
            self.section_detect_flags.extend(None if frame_res is None else 1 for frame_res in ans)

            self.state = self.State.OUT_OF_SECTION

            self.parse(is_over=True)

        self.immediate_frames.clear()
        self.deferred_frames.clear()

    def _finish_fog(self) -> None:
        # 对最后一个需要检测的帧重复add_frame_fog中的操作
        ans = detect_fog_with_batch([
            frame for _, _, frame in self.immediate_frames
        ], FOG_DETECTION_BATCH_SIZE, conf_thres=0.3)

        if self.state == self.State.IN_SECTION or self._found_screen(ans):
            self.section_info[0].extend(self.immediate_frames)
            self.section_info[1].extend(self.deferred_frames)
            self.section_info[2].extend(ans)
            self.section_detect_flags.extend(None if frame_res is None else 1 for frame_res in ans)

            self.state = self.State.OUT_OF_SECTION

            self.parse_fog(is_over=True)

        self.immediate_frames.clear()
        self.deferred_frames.clear()

    def _found_screen(self, flags) -> bool:
        # print("flags:", flags)
        return any(flag is not None for flag in flags)

    def _section_is_over(self) -> bool:
        tail_frames = SCREEN_DETECTION_TAIL_TIME * SCREEN_DETECTION_FREQUENCY
        return not self._found_screen(self.section_detect_flags[- tail_frames:])

    def _section_is_over_fog(self) -> bool:
        tail_frames = FOG_DETECTION_TAIL_TIME * FOG_DETECTION_FREQUENCY
        return not self._found_screen(self.section_detect_flags[- tail_frames:])

    def parse(self, is_over: bool=True) -> None:
        self.ready = True

        detected_frames = self.section_info[0]
        undetected_frames = self.section_info[1]
        detected_results = self.section_info[2]

        first_idx = index_of_first(detected_results)
        if first_idx is None:
            self.section = []

            for item in self.section_info:
                item.clear()

            if is_over:
                self.is_unfinished = False
                self.section_idx += 1
                self.section_detect_flags.clear()

            return

        last_idx = index_of_last(detected_results) + 1
        last_idx = last_idx if last_idx < len(detected_results) else last_idx - 1

        if not self.is_unfinished:
            if last_idx - first_idx < SCREEN_DETECTION_MINIMUM_DURATION * SCREEN_DETECTION_FREQUENCY:

                if self.detector is not None:
                    section_start = detected_frames[first_idx][0]
                    section_end = detected_frames[last_idx][0]

                    for (frame_no, _, frame), bbox in zip(detected_frames, detected_results):
                        if section_start <= frame_no <= section_end:
                            self.detector(False, self.section_idx, frame_no, frame, bbox)

                self.section = None
                for item in self.section_info:
                    item.clear()
                self.section_detect_flags.clear()
                return

        self.is_unfinished = not is_over

        section_start = detected_frames[first_idx][0]
        section_end = detected_frames[last_idx][0]

        section = []
        for (frame_no, msec, frame), bbox in zip(detected_frames, detected_results):
            if section_start <= frame_no <= section_end:
                section.append((frame_no, msec, frame, bbox))

        additional_frames = [(frame_no, msec, frame) for frame_no, msec, frame in undetected_frames if
                             section_start < frame_no < section_end]

        # 检测屏幕位置
        ans = detect_screen_with_batch(
            (frame for _, _, frame in additional_frames),
            SCREEN_DETECTION_BATCH_SIZE,
            self.conf_thres
        )

        for (frame_no, msec, frame), bbox in zip(additional_frames, ans):
            section.append((frame_no, msec, frame, bbox))

        # TODO: 最后很可能有空

        section.sort(key=lambda item: item[0])

        if self.detector:
            for frame_no, _, frame, bbox in section:
                self.detector(True, self.section_idx, frame_no, frame, bbox)

        self.section = section

        for item in self.section_info:
            item.clear()

        if not self.is_unfinished:
            self.section_idx += 1
            self.section_detect_flags.clear()

    def parse_fog(self, is_over: bool = True) -> None:
        self.ready = True

        detected_frames = self.section_info[0]
        undetected_frames = self.section_info[1]
        detected_results = self.section_info[2]

        first_idx = index_of_first(detected_results)
        if first_idx is None:
            self.section = []

            for item in self.section_info:
                item.clear()

            if is_over:
                self.is_unfinished = False
                self.section_idx += 1
                self.section_detect_flags.clear()

            return

        last_idx = index_of_last(detected_results) + 1
        last_idx = last_idx if last_idx < len(detected_results) else last_idx - 1

        if not self.is_unfinished:
            if last_idx - first_idx < FOG_DETECTION_MINIMUM_DURATION * FOG_DETECTION_FREQUENCY:

                if self.detector is not None:
                    section_start = detected_frames[first_idx][0]
                    section_end = detected_frames[last_idx][0]

                    for (frame_no, _, frame), bbox in zip(detected_frames, detected_results):
                        if section_start <= frame_no <= section_end:
                            self.detector(False, self.section_idx, frame_no, frame, bbox)

                self.section = None
                for item in self.section_info:
                    item.clear()
                self.section_detect_flags.clear()
                return

        self.is_unfinished = not is_over

        section_start = detected_frames[first_idx][0]
        section_end = detected_frames[last_idx][0]

        section = []
        for (frame_no, msec, frame), bbox in zip(detected_frames, detected_results):
            if section_start <= frame_no <= section_end:
                section.append((frame_no, msec, frame, bbox))

        additional_frames = [(frame_no, msec, frame) for frame_no, msec, frame in undetected_frames if
                             section_start < frame_no < section_end]

        # 检测屏幕位置
        ans = detect_fog_with_batch(
            (frame for _, _, frame in additional_frames),
            FOG_DETECTION_BATCH_SIZE,
            conf_thres=0.3
        )

        for (frame_no, msec, frame), bbox in zip(additional_frames, ans):
            section.append((frame_no, msec, frame, bbox))

        # TODO: 最后很可能有空

        section.sort(key=lambda item: item[0])

        if self.detector:
            for frame_no, _, frame, bbox in section:
                self.detector(True, self.section_idx, frame_no, frame, bbox)

        self.section = section

        for item in self.section_info:
            item.clear()

        if not self.is_unfinished:
            self.section_idx += 1
            self.section_detect_flags.clear()


class FogDetector:
    class BatchCache:
        def __init__(self, batch_size: int) -> None:
            self.batch_size = batch_size
            self._frames = []
            self._nones = []

        def push(self, frame_no: int, frame: Optional[np.ndarray]) -> None:
            if frame is None:
                self._nones.append((frame_no, None))
            else:
                self._frames.append((frame_no, frame))

        def is_full(self) -> bool:
            return len(self._frames) == self.batch_size

        def frames(self) -> List:
            return [frame for frame_no, frame in self._frames]

        def join_nones(self, results, clear=True) -> List:
            joined = [(frame_no, ans) for (frame_no, frame), ans in zip(self._frames, results)] + self._nones
            joined.sort(key=lambda re: re[0])

            if clear:
                self.clear()

            return joined

        def clear(self) -> None:
            self._frames.clear()
            self._nones.clear()

    def __init__(self) -> None:

        # 保存检测出fog的第一个和最后一个帧的no与msec
        self.first_frame_no = None
        self.last_frame_no = None
        self.start_msec = None
        self.end_msec = None

        self.last_psection = None

        self.result = 0

    def push_partial_section(self, is_over: bool, psection):
        if psection:
            self.last_psection = psection

        if self.first_frame_no is None:
            first_frame_idx = index_of_first(psection, lambda item: item[3])
            self.first_frame_no = psection[first_frame_idx][0]
            self.start_msec = psection[first_frame_idx][1]

        last_frame_index = index_of_last(psection, lambda item: item[3])
        if last_frame_index is not None:
            self.last_frame_no = psection[last_frame_index][0]
            self.end_msec = psection[last_frame_index][1]

    def get_results(self) -> Tuple[Any, Any, Any, Any, Any, Any, Optional[Any], Any, Any]:

        self.result = 1
        frame_no = self.first_frame_no
        percentage = 1

        frame = None

        for p_fn, _, p_frame, _ in self.last_psection:
            if p_fn == frame_no:
                frame = p_frame
                break
        # print('frame_no：', frame_no)
        # print('frame返回：', frame)

        return self.first_frame_no, self.last_frame_no, self.start_msec, self.end_msec, self.result, percentage, frame, frame_no, frame_no * self.start_msec / self.first_frame_no


# 屏幕状态种类，按顺序分别是：
# 合格、荧光粉残留、锥体玻璃残留、碎屏、荧光粉水印、荧光粉白印
class SECTION_CATEGORY(enum.Enum):
    PASS = 0
    PHOSPHOR_RESIDUE = 1
    CONE_RESIDUE = 2
    BROKEN = 3
    PHOSPHOR_WATER = 4
    PHOSPHOR_WHITE = 5


class Classifier:
    class BatchCache:
        def __init__(self, batch_size: int) -> None:
            self.batch_size = batch_size
            self._frames = []
            self._nones = []

        def push(self, frame_no: int, frame: Optional[np.ndarray]) -> None:
            if frame is None:
                self._nones.append((frame_no, None))
            else:
                self._frames.append((frame_no, frame))

        def is_full(self) -> bool:
            return len(self._frames) == self.batch_size

        def frames(self) -> List:
            return [frame for frame_no, frame in self._frames]

        def join_nones(self, results, clear=True) -> List:
            joined = [(frame_no, ans) for (frame_no, frame), ans in zip(self._frames, results)] + self._nones
            joined.sort(key=lambda re: re[0])

            if clear:
                self.clear()

            return joined

        def clear(self) -> None:
            self._frames.clear()
            self._nones.clear()

    def __init__(self,
                 detector: Callable[[int, np.ndarray, Tuple, Optional[float], Optional[float]], None] = None) -> None:
        # self.frames_in_1s = SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO

        self.broken_frame_cache = Classifier.BatchCache(BROKEN_DETECTION_BATCH_SIZE)  # 碎屏图像帧
        self.phosphor_frame_cache = Classifier.BatchCache(PHOSPHOR_DETECTION_BATCH_SIZE)  # 荧光粉残留图像帧
        self.cone_frame_cache = Classifier.BatchCache(CONE_DETECTION_BATCH_SIZE)  # 锥屏分类帧

        self.broken_detection_results = []
        self.phosphor_detection_results = []
        self.cone_detection_results = []

        # 保存检测出屏面玻璃的第一个和最后一个帧的no与msec
        self.first_frame_no = None
        self.last_frame_no = None
        self.start_msec = None
        self.end_msec = None

        self.tail_frames = []
        self.last_psection = None

        self.result = SECTION_CATEGORY.PASS

        self.detector = detector

    def push_partial_section(self, is_over: bool, psection):
        if psection:
            self.last_psection = psection

        if self.first_frame_no is None:
            # 找到第一个检测到屏面玻璃的帧的索引idx
            first_frame_idx = index_of_first(psection, lambda item: item[3])
            self.first_frame_no = psection[first_frame_idx][0]
            self.start_msec = psection[first_frame_idx][1]

        last_frame_index = index_of_last(psection, lambda item: item[3])
        if last_frame_index is not None:
            self.last_frame_no = psection[last_frame_index][0]
            self.end_msec = psection[last_frame_index][1]

        if self._finished():
            return

        # 遍历批次帧，判断是否存在碎屏和荧光粉残留
        frame_amount = len(psection)
        for frame_idx, (frame_no, msec, frame, bbox) in enumerate(psection):
            is_last_frame = frame_idx + 1 == frame_amount and (
                is_over or self.detector is not None
            )
            # 判断是否有碎屏和荧光粉残留
            self._push_frame(frame_no, frame, bbox, is_last_frame)

            # 将尾部帧加入检测，用于判断锥屏分离
            self.tail_frames.append((frame_no, frame, bbox))

            if self._finished():
                break

        self.tail_frames = self.tail_frames[- 3 * SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO:]

        # 如果当前视频遍历完毕，再判断是否锥屏分离
        if is_over:
            for idx, (frame_no, frame, bbox) in enumerate(self.tail_frames):
                screen = self._crop_screen(frame, bbox)

                self.cone_frame_cache.push(frame_no, screen)

                if self.cone_frame_cache.is_full() or idx + 1 == len(self.tail_frames):
                    # 判断锥屏是否分离-------------------->
                    cone_batch_ans = segment_cone_with_batch(self.cone_frame_cache.frames(), CONE_DETECTION_BATCH_SIZE)
                    cone_batch_ans = [(mask, np.sum(mask) // 255) for mask in cone_batch_ans]
                    cache_results = self.cone_frame_cache.join_nones(cone_batch_ans, clear=True)
                    self.cone_detection_results.extend(cache_results)

        if self.detector is not None:
            # TODO: 添加分割结果
            # assert len(self.phosphor_detection_results) == len(psection)
            # assert len(self.broken_detection_results) == len(psection)
            # assert len(self.broken_detection_results) == len(self.phosphor_detection_results)

            segment_map = dict(self.cone_detection_results)
            phosphor_map = dict(self.phosphor_detection_results)
            for frame_no, msec, frame, bbox in psection:
                segment_ans = segment_map.get(frame_no, None)
                phosphor_ans = phosphor_map.get(frame_no, None)
                self.detector(frame_no, frame, bbox, phosphor_ans,
                              segment_ans if segment_ans is None else segment_ans[0])

    # 根据每一帧保存的检测结果进行最后的判断并输出
    def classify(self) -> Tuple[Any, Any, Any, Any, SECTION_CATEGORY, Any, Optional[Any], Any, Any]:
        # 判断是否碎屏
        is_broken, broken_frame_no = self._broken_examination()
        if is_broken:
            self.result = SECTION_CATEGORY.BROKEN
            frame_no = broken_frame_no
        else:
            # 判断是否有锥体玻璃残留
            has_cone_residue, cone_residue_frame_no = self._cone_residue_examination()
            has_cone_residue = False
            if has_cone_residue:
                self.result = SECTION_CATEGORY.CONE_RESIDUE
                frame_no = cone_residue_frame_no
            else:
                # 判断是否有荧光粉残留
                has_phosphor_residue, phosphor_residue_frame_no = self._phosphor_residue_examination()
                if has_phosphor_residue:
                    self.result = SECTION_CATEGORY.PHOSPHOR_RESIDUE
                    frame_no = phosphor_residue_frame_no
                else:
                    frame_no = phosphor_residue_frame_no

                # if has_phosphor_residue == 1:
                #     self.result = SECTION_CATEGORY.PHOSPHOR_RESIDUE
                #     frame_no = phosphor_residue_frame_no
                # elif has_phosphor_residue == 2:
                #     self.result = SECTION_CATEGORY.PHOSPHOR_WATER
                #     frame_no = phosphor_residue_frame_no
                # elif has_phosphor_residue == 3:
                #     self.result = SECTION_CATEGORY.PHOSPHOR_WHITE
                #     frame_no = phosphor_residue_frame_no
                # else:
                #     frame_no = phosphor_residue_frame_no

        # 缺陷检测优先级：碎屏＞锥体玻璃残留＞荧光粉残留
        # if self._broken_examination():
        #     self.result = SECTION_CATEGORY.BROKEN
        # elif self._cone_residue_examination():
        #     self.result = SECTION_CATEGORY.CONE_RESIDUE
        # elif self._phosphor_residue_examination():
        #     self.result = SECTION_CATEGORY.PHOSPHOR_RESIDUE

        # 判断锥体玻璃含量百分比
        cone_percentage = 0
        if self.result == SECTION_CATEGORY.CONE_RESIDUE:
            cone_idx = index_of_last(
                self.cone_detection_results,
                func=lambda cnt: cnt is not None and cnt != 0,
                key=lambda cone_ans: None if cone_ans is None else cone_ans[1]
            )
            cone_percentage = np.sum(self.cone_detection_results[cone_idx][1][1]) / (256 * 256 / 1.44) * 100

        # TODO
        # fn, frame = -1, None
        #
        # for fn, _, frame, _ in self.last_psection:
        #     if fn == frame_no:
        #         break
        #
        # if fn != frame_no:
        #     frame = None

        frame = None

        for p_fn, _, p_frame, _ in self.last_psection:
            if p_fn == frame_no:
                frame = p_frame
                break

        # print('frame返回：', frame)

        return self.first_frame_no, self.last_frame_no, self.start_msec, self.end_msec, self.result, cone_percentage, frame, frame_no, frame_no * self.start_msec / self.first_frame_no

    @staticmethod
    def _crop_screen(frame, bbox) -> np.ndarray:
        if bbox is not None:
            *bbox, conf, cls = bbox
            l, t, r, b = bbox
            width = 1.2 * max((r - l), (b - t))
            screen = crop_square(frame, bbox, width)
        else:
            screen = None

        return screen

    def _finished(self) -> bool:
        ...
        return False

    def _broken_examination(self) -> bool:
        tail_range = int(round(1.5 * SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO))
        sub_res = self.broken_detection_results[-tail_range:]
        broken_max_len, broken_last = max_seq_len_with_torlenance(sub_res, 1,
                                                                  lambda ans: ans[1] is None or ans[1] > 0.5)
        not_broken_max_len, not_broken_last = max_seq_len_with_torlenance(sub_res, 1,
                                                                          lambda ans: ans[1] is None or ans[1] < 0.5)

        if broken_max_len > not_broken_max_len:
            frame_no = sub_res[broken_last][0]
            return True, frame_no
        else:
            return False, -1

    def _phosphor_residue_examination(self) -> bool:
        phosphor_max_len, clean_last = max_seq_len(self.phosphor_detection_results, lambda ans: ans[1] is not None and ans[1] < 0.5)

        # pass_max_len, clean_last = max_seq_len(self.phosphor_detection_results, idx=0)
        # phosphor_max_len, phosphor_last = max_seq_len(self.phosphor_detection_results, idx=1)
        # phosphor_water_max_len, phosphor_water_last = max_seq_len(self.phosphor_detection_results, idx=2)
        # phosphor_white_max_len, phosphor_white_last = max_seq_len(self.phosphor_detection_results, idx=3)
        threshold = SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO

        # 连续干净的屏面玻璃帧数小于阈值，判定为有荧光粉残留
        if phosphor_max_len <= threshold:
            last = index_of_last(self.phosphor_detection_results, lambda ans: ans[1] is not None and ans[1] >= 0.5)
            frame_no = self.phosphor_detection_results[last][0]
            return True, frame_no
        else:
            frame_no = self.phosphor_detection_results[clean_last][0]
            return False, frame_no

        # if pass_max_len <= threshold:
        #     lens = [phosphor_max_len, phosphor_water_max_len, phosphor_white_max_len]
        #     i = lens.index(max(lens))
        #     if i == 0:
        #         # last = index_of_last(self.phosphor_detection_results, lambda ans: ans[1] is not None and np.argmax(ans[1])==(i+1))
        #         frame_no = self.phosphor_detection_results[phosphor_last][0]
        #     elif i == 1:
        #         frame_no = self.phosphor_detection_results[phosphor_water_last][0]
        #     else:
        #         frame_no = self.phosphor_detection_results[phosphor_white_last][0]
        #     # last = index_of_last(self.phosphor_detection_results, lambda ans: ans[1] is not None and ans[1] >= 0.5)
        #     # frame_no = self.phosphor_detection_results[last][0]
        #     return i + 1, frame_no
        # else:
        #     frame_no = self.phosphor_detection_results[clean_last][0]
        #     return 0, frame_no

    def _cone_residue_examination(self) -> bool:
        cone_res = [(frame_no, None if cone_ans is None else cone_ans[1]) for frame_no, cone_ans in self.cone_detection_results]
        tail_range = int(round(1.5 * SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO))
        sub_res = cone_res[-tail_range:]
        cone_max_len, cone_last = max_seq_len_with_torlenance(sub_res, 1, key=lambda ans: ans[1])
        not_cone_max_len, not_cone_last = max_seq_len_with_torlenance(sub_res, 1, key=lambda ans: ans[1] == 0 if ans[1] is not None else None)

        if cone_max_len > not_cone_max_len and cone_max_len >= SCREEN_DETECTION_FREQUENCY * DIAGNOSIS_MAGNIFICATION_RATIO:
            while sub_res[cone_last][1] is None:
                cone_last -= 1
            frame_no = sub_res[cone_last][0]
            return True, frame_no
        else:
            return False, -1

    # 判断当前帧中是否存在碎屏和荧光粉残留
    def _push_frame(self, frame_no, frame, bbox, is_last_frame) -> None:
        screen = self._crop_screen(frame, bbox)  # 将屏面玻璃分割出来

        # 使用resnet判断是否存在碎屏-------------------->
        self.broken_frame_cache.push(frame_no, screen)
        if self.broken_frame_cache.is_full() or is_last_frame:
            broken_batch_ans = classify_broken_with_batch(self.broken_frame_cache.frames(), BROKEN_DETECTION_BATCH_SIZE)
            cache_results = self.broken_frame_cache.join_nones(broken_batch_ans, clear=True)
            self.broken_detection_results.extend(cache_results)

        # 使用resnet模型判断是否有荧光粉残留-------------------->
        self.phosphor_frame_cache.push(frame_no, screen)
        if self.phosphor_frame_cache.is_full() or is_last_frame:
            phosphor_batch_ans = classify_state_with_batch(self.phosphor_frame_cache.frames(),PHOSPHOR_DETECTION_BATCH_SIZE)
            cache_results = self.phosphor_frame_cache.join_nones(phosphor_batch_ans, clear=True)
            self.phosphor_detection_results.extend(cache_results)
