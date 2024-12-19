_fedora_common = [
    "automake",
    "libtool",
    "cmake",
    "git",
    "subversion",
    "ccache",
    "pkgconf-pkg-config",
    "gcc-c++",
    "gettext-devel",
]

_debian_common = [
    "automake",
    "libtool",
    "cmake",
    "git",
    "subversion",
    "ccache",
    "pkg-config",
    "gcc",
    "autopoint",
]

_debian_qt5 = {
    "COMMON": _debian_common + ["libbz2-dev", "libmagic-dev"],
    "zlib": ["zlib1g-dev"],
    "uuid": ["uuid-dev"],
    "libmicrohttpd": ["libmicrohttpd-dev", "ccache"],
    "qt": ["libqt5gui5", "qtbase5-dev", "qt5-default"],
    "qtwebengine": ["qtwebengine5-dev"],
    "aria2": ["aria2"],
}

_debian_qt6 = {
    "COMMON": _debian_common,
    "zlib": ["zlib1g-dev"],
    "uuid": ["uuid-dev"],
    "libmicrohttpd": ["libmicrohttpd-dev", "ccache"],
    "qt": ["qt6-base-dev", "qt6-base-dev-tools", "libqt6webenginecore6-bin", "libqt6svg6", "qtchooser"],
    "qtwebengine": ["qt6-webengine-dev"],
    "aria2": ["aria2"],
}

PACKAGE_NAME_MAPPERS = {
    "flatpak": {
        "zlib": True,
        "lzma": True,
        "icu4c": True,
        "qt": True,
        "qtwebengine": True,
        "uuid": True,
        "libxml2": True,
        "libssl": True,
        "libcurl": True,
    },
    "fedora_native_dyn": {
        "COMMON": _fedora_common,
        "uuid": ["libuuid-devel"],
        "xapian-core": None,  # Not the right version on fedora 25
        "pugixml": None,  # ['pugixml-devel'] but package doesn't provide pkg-config file
        "libmicrohttpd": ["libmicrohttpd-devel"],
        "zlib": ["zlib-devel"],
        "lzma": ["xz-devel"],
        "icu4c": None,
        "zimlib": None,
        "file": ["file-devel"],
        "gumbo": ["gumbo-parser-devel"],
        "aria2": ["aria2"],
        "qt": ["qt5-qtbase-devel", "qt5-qtsvg"],
        "qtwebengine": ["qt5-qtwebengine-devel"],
    },
    "fedora_native_static": {
        "COMMON": _fedora_common + ["glibc-static", "libstdc++-static"],
        "lzma": ["xz-devel", "xz-static"],
        # Either there is no packages, or no static or too old
    },
    "fedora_i586_dyn": {
        "COMMON": _fedora_common + ["glibc-devel.i686", "libstdc++-devel.i686"],
    },
    "fedora_i586_static": {
        "COMMON": _fedora_common + ["glibc-devel.i686"],
    },
    "fedora_armhf_static": {"COMMON": _fedora_common},
    "fedora_armhf_dyn": {"COMMON": _fedora_common},
    "fedora_android": {"COMMON": _fedora_common},
    "debian_native_dyn": _debian_qt5,
    "debian_native_static": {
        "COMMON": _debian_common + ["libbz2-dev", "libmagic-dev"],
    },
    "debian_i586_dyn": {
        "COMMON": _debian_common
        + ["libc6-dev-i386", "lib32stdc++6", "gcc-multilib", "g++-multilib"],
    },
    "debian_i586_static": {
        "COMMON": _debian_common
        + ["libc6-dev-i386", "lib32stdc++6", "gcc-multilib", "g++-multilib"],
    },
    "debian_armhf_static": {
        "COMMON": _debian_common,
    },
    "debian_armhf_dyn": {
        "COMMON": _debian_common,
    },
    "debian_android": {
        "COMMON": _debian_common,
    },
    "ubuntu_jammy_native_dyn":    _debian_qt5,
    "ubuntu_noble_native_dyn":    _debian_qt6,
    "ubuntu_oracular_native_dyn": _debian_qt6,
    "ubuntu_native_static": {
        "COMMON": _debian_common + ["libbz2-dev", "libmagic-dev"],
    },
    "Darwin_native_dyn": {
        "COMMON": ["autoconf", "automake", "libtool", "cmake", "pkg-config"],
        "file": ["libmagic"],
    },
    "Darwin_iOS": {
        "COMMON": ["autoconf", "automake", "libtool", "cmake", "pkg-config"],
        "file": ["libmagic"],
    },
}
