from .base import ConfigInfo, MixedMixin

from kiwixbuild.utils import pj
from kiwixbuild._global import option, neutralEnv
from kiwixbuild.configs.ios import MIN_MACOS_VERSION


class NativeConfigInfo(ConfigInfo):
    build = "native"

    def get_env(self):
        env = super().get_env()
        if neutralEnv("distname") == "fedora":
            env["QT_SELECT"] = "5-64"
        if neutralEnv("distname") == "Darwin":
            env["CFLAGS"] += f"-mmacosx-version-min={MIN_MACOS_VERSION}"
        return env


class NativeDyn(NativeConfigInfo):
    name = "native_dyn"
    static = False
    compatible_hosts = ["fedora", "debian", "Darwin"]


class NativeStatic(NativeConfigInfo):
    name = "native_static"
    static = True
    compatible_hosts = ["fedora", "debian"]


class NativeMixed(MixedMixin("native_static"), NativeConfigInfo):
    name = "native_mixed"
    static = False
    compatible_hosts = ["fedora", "debian", "Darwin"]
