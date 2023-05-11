from os import path
import cv2
from pathlib import Path
import matplotlib.pyplot as plt

from datetime import datetime

import utility.config
from utility.video import Video, VideoWriter
from utility import dip
from utility.dataset import *
from utility.processer import *
from utility.test_utils import *


utility.config.update_detection_weight('mbest')
utility.config.update_valid_weight('280782_model_best')
# utility.config.update_state_weight('801802_model_best')
utility.config.update_state_weight('802311_model_best')
utility.config.update_segment_weight('CE_Net_276_8')


class SectionalizerDetector:
    def __init__(self, dest_dir) -> None:
        self.dest_dir = Path(dest_dir)
        self.dest_dir.mkdir(exist_ok=True)

    def __call__(self, in_section, section_idx, frame_no, frame, bbox) -> None:
        if bbox is None or not in_section:
            return

        section_dir = self.dest_dir / f'{section_idx:02}'
        section_dir.mkdir(exist_ok=True)

        detection_dir = section_dir / 'detection'
        detection_dir.mkdir(exist_ok=True)

        *box, conf, cls = bbox
        contents = [
            (f'{conf:.2}', 'lt0')
        ]
        drawed = dip.rectangle_and_text(frame, box, contents, font_size=25, bgcolor=(108, 210, 101))
        cv2.imwrite(str(detection_dir / f'{frame_no:05}.jpg'), drawed)


class ClassifierDetector:
    def __init__(self, dest_dir):
        self.dest_dir = Path(dest_dir)
        self.dest_dir.mkdir(exist_ok=True)

        self.frames_info = []

    def __call__(self, frame_no, frame, bbox, phosphor_ans, cone_ans):
        self.frames_info.append((frame_no, frame, bbox, phosphor_ans, cone_ans))

    def save_result(self):
        draw_dir = self.dest_dir / 'frames'
        draw_dir.mkdir(exist_ok=True)

        segment_dir = self.dest_dir / 'segment'
        segment_dir.mkdir(exist_ok=True)

        broken_results, phosphor_results, cone_results = [], [], []

        for frame_no, frame, bbox, phosphor_ans, cone_ans in self.frames_info:
            # broken_results.append((frame_no, broken_ans))
            phosphor_results.append((frame_no, phosphor_ans))
            cone_results.append((frame_no, cone_ans))

            if bbox is not None:
                drawfile = draw_dir / f'{frame_no:05}.jpg'
                contents = [
                    ([
                        # f"{'NOT_VALID' if broken_ans > 0.5 else 'VALID'} ({broken_ans:.2})",
                        # TODO:
                        f"{'FAIL' if phosphor_ans > 0.5 else 'PASS'} ({phosphor_ans:.2})",
                    ], 'lt0')
                ]
                drawed = dip.rectangle_and_text(frame, bbox[:4], contents, font_size=15, bgcolor=(108, 210, 101))

                cv2.imwrite(str(drawfile), drawed)

                if cone_ans is not None:
                    segment_file = segment_dir / f'{frame_no:05}.jpg'
                    cv2.imwrite(str(segment_file), cone_ans)

        plot_dir = self.dest_dir / 'pt'
        plot_dir.mkdir(exist_ok=True)

        x = [frame_no for frame_no, _ in phosphor_results]
        y = [0.5 if ans is None else ans for _, ans in phosphor_results]
        none_y = [0.5 for _ in phosphor_results]

        plt.plot(x, y)
        plt.plot(x, none_y)
        plt.title('phosphor detection')
        plt.savefig(str(plot_dir / 'phosphor.jpg'))

        plt.clf()

        x = [frame_no for frame_no, _ in cone_results]
        y = [-100 if ans is None else np.sum(ans) // 255 for _, ans in cone_results]
        none_y = [-100 for _ in cone_results]

        plt.plot(x, y)
        plt.plot(x, none_y)
        plt.title('cone detection')
        plt.savefig(str(plot_dir / 'cone.jpg'))

        plt.clf()

        with open(str(plot_dir / 'results.txt'), 'w', encoding='utf-8') as f:
            f.write('frame numbers\n')
            f.write(', '.join(str(frame_no) for frame_no, ans in broken_results))
            f.write('\n')

            f.write('phosphor\n')
            f.write(', '.join(str(ans) for frame_no, ans in phosphor_results))
            f.write('\n')

            f.write('cone\n')
            f.write(', '.join(str(np.sum(ans) if ans is not None else -1) for frame_no, ans in cone_results))
            f.write('\n')


class Arbiter:
    '''
        检测视频并保存结果
    '''

    def __init__(self, detection_conf, save_dir=None, use_detectors: bool=False) -> None:
        self.detection_conf = detection_conf  # yolo模型置信度
        self.save_dir = save_dir
        self.use_detectors = use_detectors

    def arbitrate(self, video_path: str, verbose=False, progress_queue=None, type='tv'):
        print(f'start: {datetime.now().strftime("%H-%M-%S")}')
        print('detect video type:{}'.format(type))
        sectionalizer_detector = SectionalizerDetector(self.save_dir) if self.use_detectors else None

        frame_filter = FrameFilter(video_path, set_end_flag=True)  # 获取视频帧
        sectionalizer = Sectionalizer(self.detection_conf, sectionalizer_detector)  # 保存序列化帧(按间隔划分)
        # fps = frame_filter.computed_fps

        section_results = []  # 保存序列化检测结果
        fog_section_results = []  # 保存序列化检测结果

        section_idx = 0

        _enum = tqdm.tqdm(frame_filter) if verbose else frame_filter

        classifier_detector = ClassifierDetector(path.join(self.save_dir, f'{section_idx:02}')) if self.use_detectors else None
        # 创建分类器，用于视频帧图像的状态分类
        classifier = Classifier(classifier_detector)
        # classifier_fog = Classifier(classifier_detector)

        # 遍历视频并批量获取帧
        for i, (tag, frame_idx, msec, frame) in enumerate(_enum):
            if progress_queue is not None:
                progress_queue.put((i, len(frame_filter)))

            # 将当前帧添加到序列中，使用yolo模型检测屏面玻璃位置并保存到frame中
            sectionalizer.add_frame(tag, frame_idx, msec, frame, video_type=type)
            # sectionalizer.add_frame_fog(tag, frame_idx, msec, frame, type=type)

            if sectionalizer.is_ready():
                # 从序列中获取帧
                is_over, psection = sectionalizer.retrieve_section()

                if psection is None:
                    continue

                # 将当前批次帧送入检测器进行检测
                if type=='tv':
                    classifier.push_partial_section(is_over, psection)
                else:
                    classifier.push_partial_section_fog(is_over, psection)

                # 如果当前视频到达末尾
                if is_over:
                    if type=='tv':
                        # 根据之前检测缓存的结果，调用classify函数判断输出最近检测结果
                        start_frame_no, end_frame_no, start_msec, end_msec, section_cat, percentage, key_frame, frame_no, frame_msec = classifier.classify()

                        if classifier_detector is not None:
                            classifier_detector.save_result()

                        section_results.append((
                            start_frame_no, end_frame_no, start_msec, end_msec, section_cat, percentage, key_frame, frame_no, frame_msec
                        ))

                        if verbose:
                            print(f'{section_idx:02}:', section_results[-1])
                    else:
                        # 根据之前检测缓存的结果，调用classify函数判断输出最近检测结果
                        start_frame_no, end_frame_no, start_msec, end_msec, section_cat, percentage, key_frame, frame_no, frame_msec = classifier.classify_fog()

                        if classifier_detector is not None:
                            classifier_detector.save_result()

                        fog_section_results.append((
                            start_frame_no, end_frame_no, start_msec, end_msec, section_cat, percentage, key_frame,
                            frame_no, frame_msec
                        ))

                        if verbose:
                            print(f'{section_idx:02}:', fog_section_results[-1])

                    section_idx += 1

                    # 更新分类器
                    classifier_detector = ClassifierDetector(path.join(self.save_dir, f'{section_idx:02}')) if self.use_detectors else None
                    classifier = Classifier(classifier_detector)

                    # if section_idx == 2:
                    #     break

        print(f'end: {datetime.now().strftime("%H-%M-%S")}')

        if progress_queue is not None:
            progress_queue.put((-1, -1))

        return section_results if type=='tv' else fog_section_results
