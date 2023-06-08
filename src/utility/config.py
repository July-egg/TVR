import os
from pathlib import Path
import json
from typing import List, Optional, Union

# 获取config文件中的内容

__app_dir = Path(__file__).resolve().parents[1]

__data_dir = __app_dir / 'app_data'
__data_dir.mkdir(exist_ok=True)

__assets_dir = __app_dir / 'assets'

loaded_config = {}


def load_config() -> None:
    global loaded_config

    config_file = __data_dir / 'config.json'
    if config_file.exists():
        with open(str(config_file), 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
    # return loaded_config


def save_config() -> None:
    global loaded_config

    config_file = __data_dir / 'config.json'
    if config_file.exists():
        os.remove(str(config_file))

    with open(str(config_file), 'x', encoding='utf-8') as f:
        json.dump(loaded_config, f, ensure_ascii=False, indent=4)


def get_default_font() -> str:
    global loaded_config

    if 'default_font' in loaded_config:
        return loaded_config['default_font']
    else:
        return os.path.join(__assets_dir, 'arial.ttf')


def _get_home_directory() -> str:
    return str(__app_dir)


def get_last_video_dir() -> str:
    global loaded_config

    if 'last_video_dir' in loaded_config:
        last_file_dir = loaded_config['last_video_dir']
        if os.path.exists(last_file_dir):
            return last_file_dir
        else:
            return _get_home_directory()
    else:
        return _get_home_directory()


def update_last_video_dir(p: Union[str, List[str]]) -> None:
    global loaded_config

    if isinstance(p, List):
        p = os.path.commonprefix(p)

    if not p:
        return

    path = Path(p)

    if not path.exists() or path.is_file():
        path = path.parent

    loaded_config['last_video_dir'] = str(path)


def get_last_save_dir() -> str:
    global loaded_config

    if 'last_save_dir' in loaded_config:
        last_save_dir = loaded_config['last_save_dir']
        if os.path.exists(last_save_dir):
            return last_save_dir
        else:
            return _get_home_directory()
    else:
        return _get_home_directory()


def update_last_save_dir(p: str) -> None:
    global loaded_config

    if not p:
        return

    loaded_config['last_save_dir'] = p


def get_detection_weight() -> str:
    global loaded_config

    if 'detection_weight' in loaded_config:
        return loaded_config['detection_weight']
    else:
        return 'yolov5s'


def get_detection_weight_yolov7() -> str:
    global loaded_config

    if 'detection_weight_yolov7' in loaded_config:
        return loaded_config['detection_weight_yolov7']
    else:
        return 'yolov7w6'


def update_detection_weight(weight: str) -> None:
    global loaded_config

    loaded_config['detection_weight'] = weight


def get_state_weight() -> str:
    global loaded_config

    if 'state_weight' in loaded_config:
        return loaded_config['state_weight']
    else:
        return 'model_best'


def update_state_weight(weight: str) -> None:
    global loaded_config

    loaded_config['state_weight'] = weight


def get_valid_weight() -> str:
    global loaded_config

    if 'valid_weight' in loaded_config:
        return loaded_config['valid_weight']
    else:
        return 'model_best'


def update_valid_weight(weight: str) -> None:
    global loaded_config

    loaded_config['valid_weight'] = weight


def get_segment_weight() -> str:
    global loaded_config

    if 'segmentation_weight' in loaded_config:
        return loaded_config['segmentation_weight']
    else:
        return 'model_best'


def update_segment_weight(weight: str) -> None:
    global loaded_config

    loaded_config['segmentation_weight'] = weight


def get_broken_weight() -> str:
    global loaded_config

    if 'broken_weight' in loaded_config:
        return loaded_config['broken_weight']
    else:
        return 'ContextSEUNet'


def update_broken_weight(weight: str) -> None:
    global loaded_config

    loaded_config['broken_weight'] = weight


def get_fog_weight() -> str:
    global loaded_config

    if 'fog_weight' in loaded_config:
        return loaded_config['fog_weight']
    else:
        return 'bbox_mAP_epoch_250'


def update_fog_weight(weight: str) -> None:
    global loaded_config

    loaded_config['fog_weight'] = weight


def get_batch_info() -> dict:
    global loaded_config

    if 'batch_info' in loaded_config:
        return loaded_config['batch_info']
    else:
        loaded_config['batch_info'] = {
            'detection': 2,
            'state_test': 32,
            'broken_test': 32,
            'segmentation': 1
        }
        return loaded_config['batch_info']


def update_batch_info(model_cat, bs) -> None:
    global loaded_config

    loaded_config['batch_info'][model_cat] = bs


def get_html_template_file() -> str:
    return str(__assets_dir / 'html_template.html')


load_config()
