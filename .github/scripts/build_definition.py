from typing import NamedTuple
import csv, io, re

# Definition of what to build.
# Array is read line by line.
# Empty cells under (OS_NAME, COMPILE_CONFIG) mean "always match" (catch all, or `.*` regex)
# Once a cell doesn't match, skip to the next line.
# Once a line matches, other lines are not read, so put more specific combination first.
# Lines composed of `-` , or `=`, or starting by `#` are ignored.
# 'B' letter means that the project is build in the CI
# 'd' letter means that the project's dependencies are build and published to be used by the project's CI.
# 'P' letter means that (build) project must be publish when we do a release.
#     (This is used to avoid two publication of the same archive)
# 'S' letter means that source code must be publish (almost by definition, S should be put only with a P)
# 'D' letter means we trigger the docker forkflow to build the docker image.
# If a cell contains several letters, all are done.
BUILD_DEF = """
    | OS_NAME   | COMPILE_CONFIG     | libzim | libkiwix | zim-tools | kiwix-tools | kiwix-desktop | platform_name           | dependency_name        |
    ==============================================================================================================================================
# Osx builds, build binaries on native_dyn and native_static. On anyother things, build only the libraries
    | macos     | native_dyn         | B      |          |           |             |               |                         | macos-x86_64-dyn       |
    | macos     | native_static      | B      |          |           |             |               | macos-x86_64            |                        |
    | macos     | native_mixed       | B      |          |           |             |               | macos-x86_64            |                        |
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
    return re.fullmatch(selector, value) is not None


class Context(NamedTuple):
    OS_NAME: str
    COMPILE_CONFIG: str

    def match(self, row):
        for key in ["OS_NAME", "COMPILE_CONFIG"]:
            context_value = getattr(self, key)
            selector = row[key]
            if not selector_match(selector, context_value):
                return False
        return True


BUILD = "B"
PUBLISH = "P"
SOURCE_PUBLISH = "S"
DEPS = "d"
DOCKER = "D"


def select_build_targets(criteria):
    from common import COMPILE_CONFIG, OS_NAME

    context = Context(COMPILE_CONFIG=COMPILE_CONFIG, OS_NAME=OS_NAME)

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

    raise ValueError("No definition match with current context.")


def get_column_value(column_name):
    from common import COMPILE_CONFIG, OS_NAME

    context = Context(COMPILE_CONFIG=COMPILE_CONFIG, OS_NAME=OS_NAME)

    reader = csv.DictReader(strip_array(BUILD_DEF), dialect=TableDialect())
    for row in reader:
        if context.match(row):
            name = row[column_name]
            return name or None

    raise ValueError("No definition match with current context.")


def get_platform_name():
    return get_column_value("platform_name")


def get_dependency_archive_name():
    return get_column_value("dependency_name")
