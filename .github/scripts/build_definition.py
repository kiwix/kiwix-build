from typing import NamedTuple
import re

class Range(NamedTuple):
    start: int
    end: int

    def is_intersect(self, other: "Self") -> bool :
        if self.end <= other.start or self.start > other.end:
            return False
        return True

    def intersect(self, other: "Self") -> "Self" :
        start = max(self.start, other.start)
        end = min(self.end, other.end)
        if start > end:
            raise ValueError("Ranges don't intersect")
        return Range(start, end)


class Cell(NamedTuple):
    data: str
    range: Range


BUILD_DEF = """
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
OS_NAME         | bionic |  osx                                        |                                                                                                                       |
DESKTOP         |                                                      | eval'True |                                                                                                           |
PLATFORM_TARGET |        |  native_mixed  | native_dyn | .*_static |   |           | flatpak | android_.* | native_mixed | .*_mixed | wasm | native_.* | .*_static | armhf_.* | aarch64_.* |   |
================================================================================================================================================================================================
libzim          | x                       |                        | x |                     | x                                           |                                               | x |
libkiwix        |        |  x             |                        | x |                     | x                         |                                                                 | x |
zim-tools       |                         | x                      |   |                                                                   | x                                             | x |
kiwix-tools     |                         | x                      |   |                                                                   | x                                             | x |
kiwix-desktop   |                                                      | x                   |                                                                                             |   |
================================================================================================================================================================================================
"""



def split_in_cells(line: str):
    start = 0
    while True:
        index = line.index('|', start)
        data = line[start:index].strip()
        yield Cell(data, Range(start, index))
        start = index+1
        if start == len(line):
            break

def parse_line(line: str):
    cells = split_in_cells(line)
    key = next(cells).data
    values = list(cells)
    return key, values

def selector_match(selector, value):
    if not selector:
        return True
    if selector.startswith("eval'"):
        selector = eval(selector[5:])
        return selector == value
    return re.fullmatch(selector, value) is not None



def select_range(context):
    current_range = Range(0, 9999999999)
    for line in BUILD_DEF.split('\n'):
        if not line or line == "-"*len(line):
            continue
        if line == "="*len(line):
            break
        (key, cells) = parse_line(line)
        found = False
        for cell in cells:
            if cell.range.end <= current_range.start or cell.range.start >= current_range.end:
                continue
            if selector_match(cell.data, context[key]):
                found = True
                current_range = current_range.intersect(cell.range)
                break
        if not found:
            raise ValueError(f"No valid value found for key: {key}")

    return current_range

def get_build_order_for_range(range: Range):
    lines = iter(BUILD_DEF.split('\n'))
    for line in lines:
        if not line:
            continue
        if line == "="*len(line):
            break

    build_orders = {}
    for line in lines:
        if not line:
            continue
        if line == "="*len(line):
            break
        (key, cells) = parse_line(line)
        for cell in cells:
            if cell.range.is_intersect(range):
                if cell.data:
                    build_orders[key] = True
                else:
                    build_orders[key] = False
                break
    return build_orders

context = {
    'DESKTOP': True,
    'OS_NAME': "fedora",
    'PLATFORM_TARGET': "native_mixed"
}


def select_build_target():
    from common import (
            PLATFORM_TARGET,
            DESKTOP,
            OS_NAME
        )
    context = {
        'DESKTOP': DESKTOP,
        'PLATFORM_TARGET': PLATFORM_TARGET,
        'OS_NAME': OS_NAME
    }
    range = select_range(context)
    build_orders = get_build_order_for_range(range)

    return [project for (project, build) in build_orders.items() if build]

