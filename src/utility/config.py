import os
from pathlib import Path
import json
from typing import List, Optional, Union

# 获取config文件中的内容

__app_dir = Path(__file__).resolve().parents[1]

__data_dir = __app_dir / 'app_data'
__data_dir.mkdir(exist_ok=True)

__assets_dir = __app_dir / 'assets'

config = {}

def load_config() -> None:
    global config

    config_file = __data_dir / 'config.json'
    if config_file.exists():
        with open(str(config_file), 'r', encoding='utf-8') as f:
            config = json.load(f)

def save_config() -> None:
    global config

    config_file = __data_dir / 'config.json'
    if config_file.exists():
        os.remove(str(config_file))

    with open(str(config_file), 'x', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def get_default_font() -> str:
    global config

    if 'default_font' in config:
        return config['default_font']
    else:
        return os.path.join(__assets_dir, 'arial.ttf')


def _get_home_directory() -> str:
    if 'HOME' in os.environ:
        return os.environ['HOME']
    else:
        return os.path.expanduser('~')


def get_last_video_dir() -> str:
    global config

    if 'last_video_dir' in config:
        last_file_dir = config['last_video_dir']
        if os.path.exists(last_file_dir):
            return last_file_dir
        else:
            return _get_home_directory()
    else:
        return _get_home_directory()


def update_last_video_dir(p: Union[str, List[str]]) -> None:
    global config

    if isinstance(p, List):
        p = os.path.commonprefix(p)

    if not p:
        return

    path = Path(p)

    if not path.exists() or path.is_file():
        path = path.parent

    config['last_video_dir'] = str(path)


def get_last_save_dir() -> str:
    global config

    if 'last_save_dir' in config:
        last_save_dir = config['last_save_dir']
        if os.path.exists(last_save_dir):
            return last_save_dir
        else:
            return _get_home_directory()
    else:
        return _get_home_directory()


def update_last_save_dir(p: str) -> None:
    global config

    if not p:
        return

    config['last_save_dir'] = p


def get_detection_weight() -> str:
    global config

    if 'detection_weight' in config:
        return config['detection_weight']
    else:
        return 'yolov5s'

def get_detection_weight_yolov7() -> str:
    global config

    if 'detection_weight_yolov7' in config:
        return config['detection_weight_yolov7']
    else:
        return 'yolov7w6'

def update_detection_weight(weight: str) -> None:
    global config

    config['detection_weight'] = weight


def get_state_weight() -> str:
    global config

    if 'state_weight' in config:
        return config['state_weight']
    else:
        return 'model_best'


def update_state_weight(weight: str) -> None:
    global config

    config['state_weight'] = weight


def get_valid_weight() -> str:
    global config

    if 'valid_weight' in config:
        return config['valid_weight']
    else:
        return 'model_best'


def update_valid_weight(weight: str) -> None:
    global config

    config['valid_weight'] = weight


def get_segment_weight() -> str:
    global config

    if 'segmentation_weight' in config:
        return config['segmentation_weight']
    else:
        return 'model_best'

def get_air_weight() -> str:
    global config

    if 'air_weight' in config:
        return config['air_weight']
    else:
        return 'model_best'


def update_segment_weight(weight: str) -> None:
    global config

    config['segmentation_weight'] = weight


def get_batch_info() -> dict:
    global config

    if 'batch_info' in config:
        return config['batch_info']
    else:
        config['batch_info'] = {
            'detection': 2,
            'state_test': 32,
            'broken_test': 32,
            'segmentation': 1
        }
        return config['batch_info']


def update_batch_info(model_cat, bs) -> None:
    global config

    config['batch_info'][model_cat] = bs


def get_html_template_file() -> str:
    return str(__assets_dir / 'html_template.html')


load_config()
