
import logging
from typing import Callable, Optional, Tuple, Union
import cv2
from numpy import ndarray
from os import path
import math
import logging


def parse_fourcc_number(n: Union[int, float]) -> str:
    n = int(n)

    fourcc = []
    for i in range(0, 32, 8):
        fourcc.append(chr(n >> i & 0xFF))

    return ''.join(fourcc)

"""
@see local: file:///C:/Users/ifuijx/Files/projects/TelevisionRecycling/codes/reference/4.4.0/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
"""
class Video:
    def __init__(self, filename: str) -> None:
        self._filename = filename
        self.cap = cv2.VideoCapture(self._filename)

        assert self.cap is not None, f'can not read {self._filename}'

        test_frames = 100

        self._has_exception = False

        for _ in range(test_frames):
            self.read()

        self._real_frame_interval = self.pos_mesc() / test_frames

        self.seek_to_start()

    def __enter__(self) -> 'Video':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        assert self.cap is not None, f'maybe close twice ({self._filename})'

        self.cap.release()

        self.cap = None

    def filename(self) -> str:
        return self._filename

    def frame_width(self) -> int:
        return int(self._query(cv2.CAP_PROP_FRAME_WIDTH))

    def frame_height(self) -> int:
        return int(self._query(cv2.CAP_PROP_FRAME_HEIGHT))

    def frame_size(self) -> Tuple[int, int]:
        '''
        (width, height)
        '''
        return self.frame_width(), self.frame_height()

    def fps(self) -> float:
        return self._query(cv2.CAP_PROP_FPS)

    def computed_fps(self) -> float:
        return 1000 / self._real_frame_interval

    # the position in milliseconds
    def pos_mesc(self) -> float:
        return self._query(cv2.CAP_PROP_POS_MSEC)

    def pos_frames(self) -> int:
        return int(self._query(cv2.CAP_PROP_POS_FRAMES))

    def pos_avi_ratio(self) -> float:
        return self._query(cv2.CAP_PROP_POS_AVI_RATIO)

    def frame_count(self) -> int:
        return int(self._query(cv2.CAP_PROP_FRAME_COUNT))

    def backend_name(self) -> str:
        return self.cap.getBackendName()

    def fourcc(self) -> int:
        return int(self._query(cv2.CAP_PROP_FOURCC))

    def forucc_str(self) -> str:
        return parse_fourcc_number(self.fourcc())

    def advance_to(self, pos: int) -> None:
        assert self.pos_frames() <= pos

        while self.pos_frames() < pos:
            self.read()

        assert self.pos_frames() == pos, f'{self._filename} can not advance to pos {pos}'

    def seek_to_start(self) -> None:
        if self.pos_frames() == 0:
            return

        self.close()
        self.cap = cv2.VideoCapture(self._filename)

    def seek_to(self, pos: int) -> None:
        '''
        may be time-consuming
        '''
        if self.pos_frames() > pos:
            self.seek_to_start()

        self.advance_to(pos)

    def _query(self, property: int) -> float:
        return self.cap.get(property)

    def _update(self, property: int, value) -> None:
        self.cap.set(property, value)

    def read(self) -> Optional[ndarray]:
        if self._has_exception:
            return None

        if self.pos_frames() >= self.frame_count():
            return None

        ret, frame = self.cap.read()
        if not ret and self.pos_frames() != self.frame_count():
            logging.warn(f"{self._filename} stopped at frame {self.pos_frames()}, not {self.frame_count()}")
            self._has_exception = True
            return None
        else:
            return frame

    def info(self) -> str:
        d = {
            'filename': path.split(self._filename)[1],
            'backend': self.backend_name(),
            'frame size': str(self.frame_size()),
            'frame count': str(self.frame_count()),
            'fps': str(self.fps()),
            'position in frames': str(self.pos_frames()),
            'position in milliseconds': str(self.pos_mesc()),
            'position in avi ratio': str(self.pos_avi_ratio())
        }
        left_len = max(map(lambda key: len(key), d))

        return '\n'.join(f'{k.rjust(left_len)}: {v}' for k, v in d.items())


class VideoProxy:
    '''
    used in functions which accept a string or a Video as video. if the argument 
    is a string, the owner of video will be this VideoProxy, otherwise the owner 
    of video will be the caller
    '''
    def __init__(self, video: Union[str, Video]) -> None:
        self._should_close = False

        if isinstance(video, str):
            video = Video(video)
            self._should_close = True

        self._video = video

    def __enter__(self) -> 'Video':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        '''
        close the video if the video is acquired by filename
        '''
        if self._should_close:
            self._video.close()

    def filename(self) -> str:
        return self._video.filename()

    def frame_width(self) -> int:
        return self._video.frame_width()

    def frame_height(self) -> int:
        return self._video.frame_height()

    def frame_size(self) -> Tuple[int, int]:
        '''
        (width, height)
        '''
        return self._video.frame_size()

    def fps(self) -> float:
        return self._video.fps()

    def computed_fps(self) -> float:
        return self._video.computed_fps()

    # the position in milliseconds
    def pos_mesc(self) -> float:
        return self._video.pos_mesc()

    def pos_frames(self) -> int:
        return self._video.pos_frames()

    def pos_avi_ratio(self) -> float:
        return self._video.pos_avi_ratio()

    def frame_count(self) -> int:
        return self._video.frame_count()

    def backend_name(self) -> str:
        return self._video.backend_name()

    def fourcc(self) -> int:
        return self._video.fourcc()

    def forucc_str(self) -> str:
        return self._video.forucc_str()

    def advance_to(self, pos: int) -> None:
        self._video.advance_to(pos)

    def seek_to_start(self) -> None:
        self._video.seek_to_start()

    def seek_to(self, pos: int) -> None:
        '''
        may be time-consuming
        '''
        self._video.seek_to(pos)

    def read(self) -> ndarray:
        return self._video.read()

    def info(self) -> str:
        return self._video.info()


class VideoWriter:
    AVI_YUV_LOSSLESS = cv2.VideoWriter_fourcc('I', '4', '2', '0')
    AVI_MPEG_1 = cv2.VideoWriter_fourcc('P', 'I', 'M', 'I')
    AVI_MPEG_4 = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
    OGV = cv2.VideoWriter_fourcc('T', 'H', 'E', 'O')
    FLV = cv2.VideoWriter_fourcc('F', 'L', 'V', 'I')
    MPEG4 = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    AVC1 = cv2.VideoWriter_fourcc('a', 'v', 'c', '1')

    def __init__(self, filename: str, width: int, height: int, fps: float, fourcc=MPEG4) -> None:
        self._writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))

        self._filename = filename
        self._fourcc = fourcc
        self._width = width
        self._height = height
        self._fps = fps

        self._pos = 0

        self._last_frame :Optional[ndarray] = None

    def __enter__(self) -> 'VideoWriter':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height

    def frame_size(self) -> int:
        '''
        (width, height)
        '''
        return self.width(), self.height()

    def fps(self) -> float:
        return self.fps

    def pos_of_next_frame(self) -> int:
        return self._pos

    def push(self, frame: ndarray) -> None:
        self._pos += 1

        self._writer.write(frame)
        self._last_frame = frame

    def close(self) -> None:
        self._writer.release()
        self._writer = None

        self._pos = -1

        self._last_frame = None


class VideoSegmentTraveler:
    FRAME_SEGMENT = 0
    MESC_SEGMENT = 1
    RATIO_SEGMENT = 2

    def __init__(self, video: Video, range, seg_type) -> None:
        '''
        the range is [start, end]
        '''
        self._video = video

        self._start = range[0]
        self._end = range[1]

        self._seg_type = seg_type

    def _is_frame_segment(self) -> bool:
        return self._seg_type == VideoSegmentTraveler.FRAME_SEGMENT

    def _is_mesc_segment(self) -> bool:
        return self._seg_type == VideoSegmentTraveler.MESC_SEGMENT

    def _is_ratio_segment(self) -> bool:
        return self._seg_type == VideoSegmentTraveler.RATIO_SEGMENT

    def run(self, handler: Callable[[Video, Tuple[int, float, float], ndarray, int, int], None]) -> None:
        '''
        call handler(video, (frame_pos, mesc_pos, ratio_pos), frame, idx, total_frames) every time find 
        frame in the specified range
        '''
        entered = False
        computed_frame_count :int = None
        idx = 0

        while True:
            pos_frames = self._video.pos_frames()
            pos_mesc = self._video.pos_mesc()
            pos_avi_ratio = self._video.pos_avi_ratio()

            frame = self._video.read()

            if frame is None:
                return

            if (self._is_frame_segment() and pos_frames > self._end or
                self._is_mesc_segment() and pos_mesc > self._end or
                self._is_ratio_segment() and pos_avi_ratio > self._end):

                break

            if (self._is_frame_segment() and pos_frames >= self._start or
                self._is_mesc_segment() and pos_mesc >= self._start or
                self._is_ratio_segment() and pos_avi_ratio >= self._start):

                if not entered:
                    entered = True

                    if self._is_frame_segment():
                        computed_frame_count = self._end - pos_frames + 1
                    elif self._is_mesc_segment():
                        cycle = 1000 / self._video.computed_fps()
                        computed_frame_count = math.ceil((self._end - pos_mesc) / cycle)
                        # adjust when the end time is n times cycle
                        if int(self._end) % int(cycle) == 0:
                            computed_frame_count += 1
                    else:
                        computed_frame_count = math.ceil((self._end - pos_avi_ratio) * self._video.frame_count())

                handler(self._video, (pos_frames, pos_mesc, pos_avi_ratio), frame, idx, computed_frame_count)

                idx += 1

        logging.warn(f'the computed frame count is wrong, {idx} != {computed_frame_count}, file: {self._video.filename()}, segment: {self._start}-{self._end}')
