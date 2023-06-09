from pathlib import Path
from xmlrpc.client import DateTime
import cv2
import json
import os
import xlwt
import numpy as np
import datetime as dtmod
from datetime import datetime, timedelta
from os import path
from typing import List, Tuple, Any

import utility.config
from utility.dip import OpenCV_to_PIL
from utility.processer import SECTION_CATEGORY
from utility.tools import StringTemplate, milliseconds_to_timedelta, seconds_to_hms, section_cat_to_string


class ImageSaver:
    def __init__(self) -> None:
        ...

    def save(self, save_dir: str, images: List[np.ndarray]) -> List[str]:
        images_dir = path.join(save_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)

        result = []

        for i, frame in enumerate(images):
            # TODO: path contains Chinese characters
            imagename = f'{i:03}.jpg'
            if frame is not None:
                image = OpenCV_to_PIL(frame)
                frame_path = path.join(images_dir, imagename)
                # cv2.imwrite(frame_path, frame)
                image.save(frame_path)
                result.append(f'./images/{imagename}')
            else:
                result.append('')

        return result


class HtmlSerializer:
    def __init__(self, xls_path: str) -> None:
        self.template_file = utility.config.get_html_template_file()
        with open(self.template_file, 'r', encoding='utf-8') as f:
            self.template_content = ''.join(f.readlines())

        self.template = StringTemplate(self.template_content)

        self.xls_path = xls_path

    def serialize(
            self,
            save_dir: str,
            videopath: str,
            fps: float,
            executor: str,
            workstation: str,
            date_time: datetime,
            memo: str,
            items: List[Tuple[int, int, float, float, SECTION_CATEGORY, float, str, int, float]]) -> Tuple[List[Tuple[str, str]], Any]:

        images_dir = path.join(save_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)

        details = self._details([
            ('检查人', executor),
            ('视频文件', Path(videopath).name),
            ('工位', workstation),
            ('视频录制时间', date_time.strftime('%Y/%m/%d %H:%M:%S')),
            ('备注', memo),
            ('文档生成时间', datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
        ])

        results = self._results(fps, date_time, items)

        title = Path(videopath).stem

        file_content = self.template.instantiation({
            'details': details,
            'results': results,
            'title': title,
            'xls_path': self.xls_path
        }, hint=['title', 'xls_path', 'details', 'results'])

        # file_content = self.template_content.replace('{{ details }}', details).replace('{{ results }}', results)

        with open(path.join(save_dir, 'summary.html'), 'w', encoding='utf-8') as f:
            f.write(file_content)

    def _details(self, kvs: List[Tuple[str, str]]) -> str:
        lines = []
        for key, value in kvs:
            lines.extend([
                '<tr>',
                f'  <td class="key">{key}：</td>',
                f'  <td>{value}</td>',
                '</tr>'
            ])

        details = '\n'.join(f'        {line}' for line in lines)

        return details

    def _results(self, fps: float, date_time: datetime, items: List[Tuple[int, int, float, float, SECTION_CATEGORY, float, str, int, float]]) -> str:
        lines = [
            '<tr>',
            '  <th>序号</th>'
            '  <th>操作时间段</th>',
            '  <th>操作时间点</th>',
            '  <th>视频时间点</th>',
            '  <th>系统判断结果</th>',
            '  <th>判断图像</th>',
            '</tr>'
        ]

        for i, (frame_start, frame_end, start_msec, end_msec, section_category, cone_percentage, frame_path, frame_no, frame_msec) in enumerate(items):
            video_start, video_end = seconds_to_hms(start_msec / 1000, use_round=True), seconds_to_hms(end_msec / 1000, use_round=True)

            operation_start_time = date_time + milliseconds_to_timedelta(start_msec)
            operation_end_time = date_time + milliseconds_to_timedelta(end_msec)
            operation_start, operation_end = operation_start_time.strftime("%H:%M:%S"), operation_end_time.strftime("%H:%M:%S")

            operation_time_point = (date_time + milliseconds_to_timedelta(frame_msec)).strftime("%H:%M:%S")

            if section_category == SECTION_CATEGORY.PASS:
                result = '合格'
            elif section_category == SECTION_CATEGORY.BROKEN:
                result = '碎屏'
            elif section_category == SECTION_CATEGORY.PHOSPHOR_RESIDUE:
                result = '荧光粉残留'
            elif section_category == SECTION_CATEGORY.CONE_RESIDUE:
                result = '锥体玻璃残留'
            # elif section_category == SECTION_CATEGORY.PHOSPHOR_WATER:
            #     result = '荧光粉(水印残留)'
            # elif section_category == SECTION_CATEGORY.PHOSPHOR_WHITE:
            #     result = '荧光粉(白印残留)'
            else:
                result = '违规操作'

            lines.extend([
                '<tr>',
                f'  <td>{i + 1}</td>',
                f'  <td>{operation_start}-{operation_end}</td>',
                f'  <td>{operation_time_point}</td>'
                f'  <td>{seconds_to_hms(frame_msec / 1000, use_round=True)}</td>',
                f'  <td>{result}</td>'
                f'  <td><img src="{frame_path}" alt="无图像" /></td>',
                '</tr>'
            ])

        results = '\n'.join(f'        {line}' for line in lines)

        return results


class JsonSerializer:
    def __init__(self) -> None:
        ...

    def serialize(
            self,
            save_dir: str,
            videopath: str,
            fps: float,
            executor: str,
            workstation: str,
            date_time: datetime,
            memo: str,
            video_type: str,
            items: List[Tuple[int, int, float, float, SECTION_CATEGORY, float, str, int, float]]) -> None:

        content = self._content(videopath, executor, workstation, date_time, memo)
        if video_type == 'tv':
            summary, proceduces = self._items(fps, date_time, items)
        else:
            summary, proceduces = self._items_fog(fps, date_time, items)
        content['Summary'] = summary
        content['Proceduces'] = proceduces

        os.makedirs(save_dir, exist_ok=True)
        with open(path.join(save_dir, 'summary.json'), 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)

    def _content(self, videopath: str, executor: str, workstation: str, date_time: datetime, memo: str) -> dict:
        return {
            'Examiner': executor,
            'VideoPath': videopath,
            'WorkStation': workstation,
            'VideoStartDateTime': date_time.strftime('%Y/%m/%d %H:%M:%S'),
            'Note': memo,
            'TimeStamp': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            'Summary': None,
            'Proceduces': None
        }

    def _items(self, fps, date_time: datetime, items: List[Tuple[int, int, float, float, SECTION_CATEGORY, float, str, int, float]]) -> Tuple[dict, dict]:
        summary = {
            'Total': len(items),
            'Pass': len([item[4] for item in items if item[4] == SECTION_CATEGORY.PASS]),
            'Broken': len([item[4] for item in items if item[4] == SECTION_CATEGORY.BROKEN]),
            'PhosphorResidue': len([item[4] for item in items if item[4] == SECTION_CATEGORY.PHOSPHOR_RESIDUE]),
            'ConeResidue': len([item[4] for item in items if item[4] == SECTION_CATEGORY.CONE_RESIDUE]),
            'PhosphorWater': len([item[4] for item in items if item[4] == SECTION_CATEGORY.PHOSPHOR_WATER]),
            'PhosphorWhite': len([item[4] for item in items if item[4] == SECTION_CATEGORY.PHOSPHOR_WHITE]),
        }
        proceduces = [
            {
                'SectionIndex': i + 1,
                'RelativeStartTime': seconds_to_hms(start_msec / 1000, use_round=False),
                'RelativeEndTime': seconds_to_hms(end_msec / 1000, use_round=False),
                'AbsoluteStartTime': (date_time + timedelta(seconds=start_msec / 1000)).strftime('%H:%M:%S'),
                'AbsoluteEndTime': (date_time + timedelta(seconds=end_msec / 1000)).strftime('%H:%M:%S'),
                'Duration': (end_msec - start_msec) / 1000,
                'ExaminationResult': section_cat_to_string(cat),
                'ResidualGlassPercentage': percentage,
                'KeyFramePath': frame_path,
                'KeyFrameTime': seconds_to_hms(frame_msec / 1000, use_round=False)
            } for i, (frame_start, frame_end, start_msec, end_msec, cat, percentage, frame_path, frame_no, frame_msec) in enumerate(items)
        ]
        return summary, proceduces

    def _items_fog(self, fps, date_time: datetime, items: List[Tuple[int, int, float, float, SECTION_CATEGORY, float, str, int, float]]) -> Tuple[dict, dict]:
        summary = {
            'Total': len(items),
            'Pass': len([item[4] for item in items if item[4] == 0]),
            'Fog': len([item[4] for item in items if item[4] == 1]),
        }
        proceduces = [
            {
                'SectionIndex': i + 1,
                'RelativeStartTime': seconds_to_hms(start_msec / 1000, use_round=False),
                'RelativeEndTime': seconds_to_hms(end_msec / 1000, use_round=False),
                'AbsoluteStartTime': (date_time + timedelta(seconds=start_msec / 1000)).strftime('%H:%M:%S'),
                'AbsoluteEndTime': (date_time + timedelta(seconds=end_msec / 1000)).strftime('%H:%M:%S'),
                'Duration': (end_msec - start_msec) / 1000,
                'ExaminationResult': 'Fog',
                # 'ResidualGlassPercentage': percentage,
                'KeyFramePath': frame_path,
                'KeyFrameTime': seconds_to_hms(frame_msec / 1000, use_round=False)
            } for i, (frame_start, frame_end, start_msec, end_msec, cat, percentage, frame_path, frame_no, frame_msec) in enumerate(items)
        ]
        return summary, proceduces


class ExcelSerializer:
    def __init__(self) -> None:
        ...

    @staticmethod
    def _proper_cell_width(content: str) -> int:
        return 256 * (len(content.encode('gb18030')) + 2)

    @staticmethod
    def _cell_style(bold: bool) -> xlwt.XFStyle:
        style = xlwt.XFStyle()
        font = xlwt.Font()

        font.bold = True

        style.font = font

        return style

    def serialize(
            self,
            save_dir: str,
            videopath: str,
            fps: float,
            executor: str,
            workstation: str,
            date_time: datetime,
            memo: str,
            video_type: str,
            items: List[Tuple[int, int, float, float, SECTION_CATEGORY, float, str, int, float]]) -> None:

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('sheet1', cell_overwrite_ok=True)

        proper_widths = [
            self._proper_cell_width('序号'),
            self._proper_cell_width('操作时间段'),
            self._proper_cell_width('操作时间点'),
            self._proper_cell_width('视频时间点'),
            self._proper_cell_width('系统判断结果')
        ]

        for i, title in enumerate(['序号', '操作时间段', '操作时间点', '视频时间点', '系统判断结果']):
            sheet.write(0, i, title, self._cell_style(bold=True))

        if video_type == 'tv':
            for i, (frame_start, frame_end, start_msec, end_msec, section_category, cone_percentage, frame_path, frame_no, frame_msec) in enumerate(items):
                operation_start_time = date_time + milliseconds_to_timedelta(start_msec)
                operation_end_time = date_time + milliseconds_to_timedelta(end_msec)
                operation_start, operation_end = operation_start_time.strftime("%H:%M:%S"), operation_end_time.strftime("%H:%M:%S")
                operation_period = f'{operation_start}-{operation_end}'

                operation_time_point = (date_time + milliseconds_to_timedelta(frame_msec)).strftime("%H:%M:%S")
                video_time_point = seconds_to_hms(frame_msec / 1000, use_round=True)

                if section_category == SECTION_CATEGORY.PASS:
                    result = '合格'
                elif section_category == SECTION_CATEGORY.BROKEN:
                    result = '碎屏'
                elif section_category == SECTION_CATEGORY.PHOSPHOR_RESIDUE:
                    result = '荧光粉残留'
                elif section_category == SECTION_CATEGORY.CONE_RESIDUE:
                    result = '锥体玻璃残留'
                elif section_category == SECTION_CATEGORY.PHOSPHOR_WATER:
                    result = '荧光粉(水印残留)'
                elif section_category == SECTION_CATEGORY.PHOSPHOR_WHITE:
                    result = '荧光粉(白印残留)'
                else:
                    result = '违规操作'

                for j, content in enumerate([str(i + 1), operation_period, operation_time_point, video_time_point, result]):
                    sheet.write(i + 1, j, content)
                    proper_widths[j] = max(proper_widths[j], self._proper_cell_width(content))
        else:
            for i, (frame_start, frame_end, start_msec, end_msec, section_category, cone_percentage, frame_path, frame_no, frame_msec) in enumerate(items):
                operation_start_time = date_time + milliseconds_to_timedelta(start_msec)
                operation_end_time = date_time + milliseconds_to_timedelta(end_msec)
                operation_start, operation_end = operation_start_time.strftime("%H:%M:%S"), operation_end_time.strftime(
                    "%H:%M:%S")
                operation_period = f'{operation_start}-{operation_end}'

                operation_time_point = (date_time + milliseconds_to_timedelta(frame_msec)).strftime("%H:%M:%S")
                video_time_point = seconds_to_hms(frame_msec / 1000, use_round=True)

                if section_category == 0:
                    result = '合格'
                elif section_category == 1:
                    result = '漏氟'
                else:
                    result = '违规操作'

                for j, content in enumerate(
                        [str(i + 1), operation_period, operation_time_point, video_time_point, result]):
                    sheet.write(i + 1, j, content)
                    proper_widths[j] = max(proper_widths[j], self._proper_cell_width(content))

        for i, width in enumerate(proper_widths):
            sheet.col(i).width = width

        xls_name = Path(videopath).stem
        workbook.save(path.join(save_dir, f'{xls_name}.xls'))


class ResultSerializer:
    def __init__(self) -> None:
        ...

    def serialize(
            self,
            save_dir: str,
            videopath: str,
            fps: float,
            executor: str,
            workstation: str,
            date_time: datetime,
            memo: str,
            video_type: str,
            items: List[Tuple[int, int, float, float, SECTION_CATEGORY, float, np.ndarray, int, float]]) -> None:

        image_saver = ImageSaver()
        image_paths = image_saver.save(save_dir, [frame for *_, frame, _, _ in items])

        save_items = [(*head, image_path, frame_no, frame_msec) for (*head, _, frame_no, frame_msec), image_path in zip(items, image_paths)]
        # if len(save_items) > 0:
        #     for save_item in save_items:
        #         print(save_item)

        json_serializer = JsonSerializer()
        json_serializer.serialize(save_dir, videopath, fps, executor, workstation, date_time, memo, video_type, save_items)

        src_dir = path.join(save_dir, '__src')
        os.makedirs(src_dir, exist_ok=True)

        excel_serializer = ExcelSerializer()
        excel_serializer.serialize(src_dir, videopath, fps, executor, workstation, date_time, memo, video_type, save_items)

        # xls_name = Path(videopath).stem
        # xls_path = path.abspath(path.join(src_dir, f'{xls_name}.xls')).replace('\\', '/')

        # html_serializer = HtmlSerializer(xls_path)
        # html_serializer.serialize(save_dir, videopath, fps, executor, workstation, date_time, memo, video_type, save_items)
