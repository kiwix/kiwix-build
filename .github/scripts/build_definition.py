from typing import NamedTuple
import csv, io, re

# Definition of what to build.
# Array is read line by line.
# Empty cells under (OS_NAME, PLATFORM_TARGET) mean "always match" (catch all, or `.*` regex)
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
    | OS_NAME | PLATFORM_TARGET    | libzim | libkiwix | zim-tools | kiwix-tools | kiwix-desktop | platform_name        |
    =====================================================================================================================
# Bionic is a special case as we need to compile libzim on old arch for python
    | bionic  | native_mixed       | BP     |          |           |             |               | linux-x86_64-bionic  |
    | bionic  | aarch64_mixed      | BP     |          |           |             |               | linux-aarch64-bionic |
    --------------------------------------------------------------------------------------------------------------------
# Osx builds, build binaries on native_dyn and native_static. On anyother things, build only the libraries
    | macos   | native_dyn         | d      | d        | dB        | B           |               |                      |
    | macos   | native_static      |        |          | BP        | BP          |               | macos-x86_64         |
    | macos   | native_mixed       | BP     | BP       |           |             |               | macos-x86_64         |
    | macos   | iOS_arm64          | dB     | B        |           |             |               |                      |
    | macos   | iOS_x86_64         | dB     | B        |           |             |               |                      |
    | macos   | macOS_arm64_static |        |          | BP        | BP          |               | macos-arm64          |
    | macos   | macOS_arm64_mixed  | BP     | BP       |           |             |               | macos-arm64          |
    | macos   | macOS_x86_64       | B      | B        |           |             |               |                      |
    ----------------------------------------------------------------------------------------------
    |         | flatpak            |        |          |           |             | BP            |                      |
    |         | native_static      | d      | d        | dBPSD     | dBPSD       |               | linux-x86_64         |
    |         | native_mixed       | BPS    | BPS      |           |             |               | linux-x86_64         |
    |         | native_dyn         | d      | d        | dB        | dB          | dBPS          |                      |
    # libzim CI is building alpine_dyn but not us
    |         | android_arm        | dBP    | dBP      |           |             |               | android-arm          |
    |         | android_arm64      | dBP    | dBP      |           |             |               | android-arm64        |
    |         | android_x86        | BP     | BP       |           |             |               | android-x86          |
    |         | android_x86_64     | BP     | BP       |           |             |               | android-x86_64       |
    |         | armv6_static       |        |          | BP        | BP          |               | linux-armv6          |
    |         | armv6_mixed        | BP     |          |           |             |               | linux-armv6          |
    |         | armv6_dyn          |        |          | B         | B           |               |                      |
    |         | armv8_static       |        |          | BP        | BP          |               | linux-armv8          |
    |         | armv8_mixed        | BP     |          |           |             |               | linux-armv8          |
    |         | armv8_dyn          |        |          | B         | B           |               |                      |
    |         | aarch64_static     |        |          | BP        | BP          |               | linux-aarch64        |
    |         | aarch64_mixed      | BP     |          |           |             |               | linux-aarch64        |
    |         | aarch64_dyn        | d      |          | B         | B           |               |                      |
    |         | aarch64_musl_static|        |          | BP        | BP          |               | linux-aarch64-musl   |
    |         | aarch64_musl_mixed | BP     |          |           |             |               | linux-aarch64-musl   |
    |         | aarch64_musl_dyn   | d      |          | B         | B           |               |                      |
    |         | x86-64_musl_static |        |          | BP        | BP          |               | linux-x86_64-musl    |
    |         | x86-64_musl_mixed  | BP     |          |           |             |               | linux-x86_64-musl    |
    |         | win32_static       | d      | dB       | dBP       | dBP         |               | win-i686             |
    |         | win32_dyn          | d      | dB       | dB        | dB          |               |                      |
    |         | i586_static        |        |          | BP        | BP          |               | linux-i586           |
    |         | i586_dyn           |        |          | B         | B           |               |                      |
    |         | wasm               | dBP    |          |           |             |               | wasm-emscripten      |
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
    PLATFORM_TARGET: str

    def match(self, row):
        for key in ["OS_NAME", "PLATFORM_TARGET"]:
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
    from common import PLATFORM_TARGET, OS_NAME

    context = Context(PLATFORM_TARGET=PLATFORM_TARGET, OS_NAME=OS_NAME)

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

def get_platform_name():
    from common import PLATFORM_TARGET, OS_NAME

    context = Context(PLATFORM_TARGET=PLATFORM_TARGET, OS_NAME=OS_NAME)

    reader = csv.DictReader(strip_array(BUILD_DEF), dialect=TableDialect())
    for row in reader:
        if context.match(row):
            name = row["platform_name"]
            return name or None

    raise "No definition match with current context."
