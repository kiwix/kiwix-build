import platform
import sys
import sysconfig
from typing import ClassVar

from kiwixbuild._global import neutral_env
from kiwixbuild.configs.apple import MIN_MACOS_VERSION

from .base import ConfigInfo, mixed_mixin


class NativeConfigInfo(ConfigInfo):
    build = "native"

    def get_env(self):
        env = super().get_env()
        if neutral_env("distname") == "fedora":
            env["QT_SELECT"] = "5-64"
        if neutral_env("distname") == "Darwin":
            env["CFLAGS"] += f"-mmacosx-version-min={MIN_MACOS_VERSION}"
        return env

    @property
    def arch_name(self):
        if sys.platform == "darwin":
            return f"{platform.machine()}-apple-darwin"
        return sysconfig.get_platform()


class NativeDyn(NativeConfigInfo):
    name = "native_dyn"
    static = False
    compatible_hosts: ClassVar[list[str]] = [
        "fedora",
        "debian",
        "ubuntu",
        "Darwin",
        "almalinux",
        "Windows",
    ]


class NativeStatic(NativeConfigInfo):
    name = "native_static"
    static = True
    compatible_hosts: ClassVar[list[str]] = [
        "fedora",
        "debian",
        "ubuntu",
        "Darwin",
        "almalinux",
        "Windows",
    ]


class NativeMixed(mixed_mixin("native_static"), NativeConfigInfo):
    name = "native_mixed"
    static = False
    compatible_hosts: ClassVar[list[str]] = [
        "fedora",
        "debian",
        "ubuntu",
        "Darwin",
        "almalinux",
        "Windows",
    ]
