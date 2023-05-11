from typing import NamedTuple
import csv, io, re

# Definition of what to build.
# Array is read line by line.
# Empty cells under (OS_NAME, DESKTOP, PLATFORM_TARGET) mean "always match" (catch all, or `.*` regex)
# Once a cell doesn't match, skip to the next line.
# Once a line matches, other lines are not read, so put more specific combination first.
# Lines composed of `-` , or `=`, or starting by `#` are ignored.
# 'B' letter means that the project is build in the CI
# 'd' letter means that the project's dependencies are build and published to be used by the project's CI.
# If a cell contains both, both are done.
BUILD_DEF = """
    | OS_NAME | DESKTOP   | PLATFORM_TARGET    | libzim | libkiwix | zim-tools | kiwix-tools | kiwix-desktop |
    =======================================================================================================
# Bionic is a special case as we need to compile libzim on old arch for python
    | bionic  |           |                    | B      |          |           |             |               |
    -------------------------------------------------------------------------------------------------------
# Osx builds, build binaries on native_dyn and native_static. On anyother things, build only the libraries
    | osx     |           | native_dyn         | d      | d        | dB        | B           |               |
    | osx     |           | native_static      |        |          | B         | B           |               |
    | osx     |           | native_mixed       | B      | B        |           |             |               |
    | osx     |           | iOS_arm64          | dB     | B        |           |             |               |
    | osx     |           | iOS_x86_64         | dB     | B        |           |             |               |
    | osx     |           | iOS_Mac_ABI        | B      | B        |           |             |               |
    | osx     |           | macOS_arm64_static | B      | B        |           |             |               |
    | osx     |           | macOS_arm64_mixed  | B      | B        |           |             |               |
    | osx     |           | macOS_x86_64       | B      | B        |           |             |               |
    -------------------------------------------------------------------------------------------------------
# Build kiwix-desktop only on specific targets
    |         | eval'True |                    |        |          |           |             | B             |
    |         |           | flatpak            |        |          |           |             | B             |
    -------------------------------------------------------------------------------------------------------
    |         |           | native_static      | d      | d        | dB        | dB          |               |
    |         |           | native_dyn         | d      | d        | dB        | dB          |               |
    |         |           | native_mixed       | B      | B        |           |             |               |
# libzim CI is building alpine_dyn but not us
    |         |           | android_arm        | dB     | dB       |           |             |               |
    |         |           | android_arm64      | dB     | dB       |           |             |               |
    |         |           | android_x86        | B      | B        |           |             |               |
    |         |           | android_x86_64     | B      | B        |           |             |               |
    |         |           | armv6_static       |        |          | B         | B           |               |
    |         |           | armv6_dyn          |        |          | B         | B           |               |
    |         |           | armv6_mixed        | B      |          |           |             |               |
    |         |           | armv8_static       |        |          | B         | B           |               |
    |         |           | armv8_dyn          |        |          | B         | B           |               |
    |         |           | armv8_mixed        | B      |          |           |             |               |
    |         |           | aarch64_static     |        |          | B         | B           |               |
    |         |           | aarch64_dyn        | d      |          | B         | B           |               |
    |         |           | aarch64_mixed      | B      |          |           |             |               |
    |         |           | win32_static       | d      | dB       | dB        | dB          |               |
    |         |           | win32_dyn          | d      | dB       | dB        | dB          |               |
    |         |           | i586_static        |        |          | B         | B           |               |
    |         |           | i586_dyn           |        |          | B         | B           |               |
    |         |           | wasm               | dB     |          |           |             |               |
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


BUILD = "B"
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
