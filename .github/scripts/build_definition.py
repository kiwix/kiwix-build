from typing import NamedTuple
import csv, io, re

# Definition of what to build.
# Array is read line by line.
# Empty cells under (OS_NAME, DESKTOP, PLATFORM_TARGET) mean "always match" (catch all, or `.*` regex)
# Once a cell doesn't match, skip to the next line.
# Once a line matches, other lines are not read, so put more specific combination first.
# Lines composed of `-` , or `=`, or starting by `#` are ignored.
BUILD_DEF = """
    | OS_NAME | DESKTOP   | PLATFORM_TARGET    | libzim | libkiwix | zim-tools | kiwix-tools | kiwix-desktop |
    =======================================================================================================
# Bionic is a special case as we need to compile libzim on old arch for python
    | bionic  |           |                    | b      |          |           |             |               |
    -------------------------------------------------------------------------------------------------------
# Osx builds, build binaries on native_dyn and native_static. On anyother things, build only the libraries
    | osx     |           | native_dyn      |        |          | b         | b           |               |
    | osx     |           | native_static   |        |          | b         | b           |               |
    | osx     |           | native_mixed       | b      | b        |           |             |               |
    | osx     |           | iOS_arm64          | b      | b        |           |             |               |
    | osx     |           | iOS_x86_64         | b      | b        |           |             |               |
    | osx     |           | iOS_Mac_ABI        | b      | b        |           |             |               |
    | osx     |           | macOS_arm64_static | b      | b        |           |             |               |
    | osx     |           | macOS_arm64_mixed  | b      | b        |           |             |               |
    | osx     |           | macOS_x86_64       | b      | b        |           |             |               |
    -------------------------------------------------------------------------------------------------------
# Build kiwix-desktop only on specific targets
    |         | eval'True |                    |        |          |           |             | b             |
    |         |           | flatpak            |        |          |           |             | b             |
    -------------------------------------------------------------------------------------------------------
    |         |           | native_static      |        |          | b         | b           |               |
    |         |           | native_dyn         |        |          | b         | b           |               |
    |         |           | native_mixed    | b      | b        |           |             |               |
    |         |           | android_arm        | b      | b        |           |             |               |
    |         |           | android_arm64      | b      | b        |           |             |               |
    |         |           | android_x86        | b      | b        |           |             |               |
    |         |           | android_x86_64     | b      | b        |           |             |               |
    |         |           | armv6_static       |        |          | b         | b           |               |
    |         |           | armv6_dyn          |        |          | b         | b           |               |
    |         |           | armv6_mixed        | b      |          |           |             |               |
    |         |           | armv8_static       |        |          | b         | b           |               |
    |         |           | armv8_dyn          |        |          | b         | b           |               |
    |         |           | armv8_mixed        | b      |          |           |             |               |
    |         |           | aarch64_static     |        |          | b         | b           |               |
    |         |           | aarch64_dyn        |        |          | b         | b           |               |
    |         |           | aarch64_mixed      | b      |          |           |             |               |
    |         |           | win32_static       |        |          | b         | b           |               |
    |         |           | win32_dyn          |        |          | b         | b           |               |
    |         |           | i586_static        |        |          | b         | b           |               |
    |         |           | i586_dyn           |        |          | b         | b           |               |
    |         |           | wasm            | b      |          |           |             |               |
"""


class TableDialect(csv.Dialect):
    delimiter = "|"
    quoting = csv.QUOTE_NONE
    lineterminator = "\n"


def strip_array(array_str):
    """Return a iterable of lines, skiping "decorative lines" and with all values in the line's cells stripped"""
    for line in array_str.splitlines():
        line = line.strip()
        line_set = set(line)
        if (
            not line
            or line.startswith("#")
            or (len(line_set) == 1 and line_set.pop() in "-=")
        ):
            continue
        yield "|".join(c.strip() for c in line.split("|"))


def selector_match(selector, value):
    if not selector:
        return True
    if selector.startswith("eval'"):
        selector = eval(selector[5:])
        return selector == value
    return re.fullmatch(selector, value) is not None


class Context(NamedTuple):
    OS_NAME: str
    DESKTOP: bool
    PLATFORM_TARGET: str

    def match(self, row):
        for key in ["OS_NAME", "DESKTOP", "PLATFORM_TARGET"]:
            context_value = getattr(self, key)
            selector = row[key]
            if not selector_match(selector, context_value):
                return False
        return True


BUILD = "b"
DEPS = "d"


def select_build_targets(criteria):
    from common import PLATFORM_TARGET, DESKTOP, OS_NAME

    context = Context(PLATFORM_TARGET=PLATFORM_TARGET, DESKTOP=DESKTOP, OS_NAME=OS_NAME)

    reader = csv.DictReader(strip_array(BUILD_DEF), dialect=TableDialect())
    for row in reader:
        if context.match(row):
            build_order = [
                k
                for k in (
                    "libzim",
                    "libkiwix",
                    "zim-tools",
                    "kiwix-tools",
                    "kiwix-desktop",
                )
                if criteria in row[k]
            ]
            print(build_order)
            return build_order

    raise "No definition match with current context."
