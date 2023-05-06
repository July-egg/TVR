import datetime
import os
from typing import Callable, List, Optional, Tuple
import numpy as np


def get_home_directory() -> Optional[str]:
    if 'HOME' in os.environ:
        return os.environ['HOME']
    else:
        return None


def index_of_first(array: List, func=None, key=None) -> Optional[int]:
    res = None
    for i, item in enumerate(array):
        if key is not None:
            item = key(item)

        is_true = func(item) if func is not None else item
        if is_true:
            res = i
            break
    return res


def index_of_last(array: List, func=None, key=None) -> Optional[int]:
    res = None
    for i in range(-1, - len(array) - 1, -1):
        item = array[i]
        if key is not None:
            item = key(item)

        is_true = func(item) if func is not None else item
        if is_true:
            res = len(array) + i
            break
    return res

# 计算最大的连续的干净的屏面玻璃帧数
# lambda ans: ans[1] is not None and ans[1] >= 0.5
def max_seq_len(array: List, func=None, key=None, idx=0) -> Tuple[int, int]:
    ans = 0
    candidate = 0

    last = 0

    seq_len = 0
    for i, item in enumerate(array):
        if key is not None:
            item = key(item)

        # 该帧荧光粉是否清除干净，array中保存的是荧光粉未清除干净的概率
        # is_true = func(item) if func is not None else item
        # 记录当前种类在帧序列中连续最大的数量
        is_true = np.argmax(item[1]) == idx if func is None else item

        if is_true:
            seq_len += 1
            candidate = i
        else:
            ans = max(ans, seq_len)
            last = candidate
            seq_len = 0
        ans = max(ans, seq_len)
        last = candidate if candidate else last
    return ans, last


def max_seq_len_with_torlenance(array: List, tolerance, func=None, key=None) -> Tuple[int, int]:
    ans = 0
    candidate = 0
    last = 0

    seq_len = 0
    tolerable = 0
    for i, item in enumerate(array):
        if key is not None:
            item = key(item)

        is_true = func(item) if func is not None else item

        if is_true:
            seq_len += 1 + tolerable
            tolerable = 0
            candidate = i

        else:
            if seq_len > 0:
                tolerable += 1

            if tolerable > tolerance:
                ans = max(ans, seq_len)
                last = candidate
                seq_len = 0
                tolerable = 0

    return max(ans, seq_len), last


def seconds_to_hms(seconds: float, use_round: bool=False) -> str:
    second = seconds % 60
    mins = int(seconds // 60)
    min = mins % 60
    hour = mins // 60

    if use_round:
        return f'{hour}:{min:02}:{int(round(second)):02}'
    else:
        return f'{hour}:{min:02}:{second:.2f}'


def milliseconds_to_timedelta(milli_seconds: float) -> datetime.timedelta:
    days = milli_seconds // (3600 * 24 * 1000)
    seconds = (milli_seconds - days * 3600 * 24 * 1000) // 1000
    milliseconds = milli_seconds % 1000

    return datetime.timedelta(days, seconds, milliseconds)


def section_cat_to_string(cat):
    from .processer import SECTION_CATEGORY

    if cat == SECTION_CATEGORY.PASS:
        return 'Pass'
    elif cat == SECTION_CATEGORY.BROKEN:
        return 'Broken'
    elif cat == SECTION_CATEGORY.CONE_RESIDUE:
        return 'ConeResidue'
    elif cat == SECTION_CATEGORY.PHOSPHOR_RESIDUE:
        return 'PhosphorResidue'


class StringTemplate:
    def __init__(self, template_content: str) -> None:
        self.content = template_content

    def instantiation(self, kvs: dict, *, hint: Optional[List[str]]=None) -> str:
        if hint is None:
            hint = list(kvs.keys())

        ans = self.content

        for key in hint:
            ans = ans.replace('{{ %s }}' % key, kvs[key])

        return ans
