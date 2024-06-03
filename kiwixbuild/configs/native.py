from .base import ConfigInfo, MixedMixin

from kiwixbuild.utils import pj
from kiwixbuild._global import option, neutralEnv
from kiwixbuild.configs.ios import MIN_MACOS_VERSION
import sysconfig
import platform
import sys


class NativeConfigInfo(ConfigInfo):
    build = "native"

    def get_env(self):
        env = super().get_env()
        if neutralEnv("distname") == "fedora":
            env["QT_SELECT"] = "5-64"
        if neutralEnv("distname") == "Darwin":
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
    compatible_hosts = ["fedora", "debian", "Darwin", "almalinux"]


class NativeStatic(NativeConfigInfo):
    name = "native_static"
    static = True
    compatible_hosts = ["fedora", "debian", "Darwin", "almalinux"]


class NativeMixed(MixedMixin("native_static"), NativeConfigInfo):
    name = "native_mixed"
    static = False
    compatible_hosts = ["fedora", "debian", "Darwin", "almalinux"]
