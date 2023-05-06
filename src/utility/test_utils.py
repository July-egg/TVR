from typing import List, Tuple
from PIL import Image, ImageDraw


def parse_elan_plain_text(filepath) -> List[Tuple[str, str, float, float]]:
    '''
    parses the annotations generated from ELAN plain text:
    clean cat, sep cat, start time, end time (the unit of time is ms)
    '''

    def _elan_time_to_milliseconds(elan_time: str) -> int:
        h, m, s = map(float, elan_time.split(':'))
        return int((h * 3600 + m * 60 + s) * 1000)

    res = []

    with open(filepath, encoding='utf-8') as f:
        line_no = 0

        while True:
            # a complete tag is constructed by four lines
            cats = [None, None]
            starts = [None, None]
            ends = [None, None]

            for i, elan_tag in enumerate(['clean', 'sep']):
                category = f.readline().rstrip()
                time_span = f.readline().rstrip()

                if not time_span:
                    return res

                category = category.split()[1]

                line_no += 2

                cats[i] = category
                starts[i], ends[i] = map(
                    _elan_time_to_milliseconds, time_span.split(' - ')
                )

            assert starts[0] == starts[1], f'inconsistent start time, <{filepath}:{line_no}>'
            assert ends[0] == ends[1], f'inconsistent end time, <{filepath}:<{line_no}>'

            res.append((*cats, starts[0], ends[0]))
