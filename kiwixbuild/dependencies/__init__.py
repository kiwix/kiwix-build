# `Dependency` must be defined before the dependency modules are imported:
# they register themselves on import and some of them import `kiwixbuild.configs`,
# which in turn needs `kiwixbuild.dependencies.Dependency`.
from .base import Dependency

# isort: split
from . import (  # noqa: F401 (imported to register the dependencies)
    all_dependencies,
    aria2,
    boostregex,
    docoptcpp,
    gumbo,
    icu4c,
    ios_fat_lib,
    kiwix_desktop,
    kiwix_tools,
    libcurl,
    libkiwix,
    libmagic,
    libmicrohttpd,
    libzim,
    lzma,
    mustache,
    pugixml,
    qt,
    tc_android_ndk,
    tc_armhf,
    tc_emsdk,
    tc_flatpak,
    tc_musl,
    uuid,
    xapian,
    zim_testing_suite,
    zim_tools,
    zlib,
    zstd,
)

__all__ = ["Dependency"]
