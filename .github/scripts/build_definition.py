from typing import NamedTuple
import csv, io, re

# Definition of what to build.
# Array is read line by line.
# Empty cells under (OS_NAME, DESKTOP, PLATFORM_TARGET) mean "always match" (catch all, or `.*` regex)
# Once a cell doesn't match, skip to the next line.
# Once a line matches, other lines are not read, so put more specific combination first.
# Lines composed of `-` , or `=`, or starting by `#` are ignored.
BUILD_DEF = """
    | OS_NAME | DESKTOP   | PLATFORM_TARGET | libzim | libkiwix | zim-tools | kiwix-tools | kiwix-desktop |
    =======================================================================================================
# Bionic is a special case as we need to compile libzim on old arch for python
    | bionic  |           |                 | x      |          |           |             |               |
    -------------------------------------------------------------------------------------------------------
# Osx builds, build binaries on native_dyn and native_static. On any other things, build only the libraries
    | osx     |           | native_dyn      |        |          | x         | x           |               |
    | osx     |           | native_static   |        |          | x         | x           |               |
    | osx     |           |                 | x      | x        |           |             |               |
    -------------------------------------------------------------------------------------------------------
# Build kiwix-desktop only on specific targets
    |         | eval'True |                 |        |          |           |             | x             |
    |         |           | flatpak         |        |          |           |             | x             |
    -------------------------------------------------------------------------------------------------------
# Library builds, on embedded archs or on all *_mixed targets
    |         |           | android_.*      | x      | x        |           |             |               |
    |         |           | native_mixed    | x      | x        |           |             |               |
    |         |           | .*_mixed        | x      |          |           |             |               |
    |         |           | wasm            | x      |          |           |             |               |
# Build binaries on *_static targets or on all others "non mixed" targets (where we have already build libs)
    |         |           | native_.*       |        |          | x         | x           |               |
    |         |           | .*_static       |        |          | x         | x           |               |
    |         |           | armv[68]_.*     |        |          | x         | x           |               |
    |         |           | aarch64_.*      |        |          | x         | x           |               |
# Else, let's build everything.
    |         |           |                 | x      | x        | x         | x           |               |
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


def select_build_targets():
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
                if row[k] == "x"
            ]
            print(build_order)
            return build_order

    raise "No definition match with current context."
