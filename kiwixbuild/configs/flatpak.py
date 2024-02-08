from .base import ConfigInfo
from kiwixbuild._global import option, neutralEnv


class FlatpakConfigInfo(ConfigInfo):
    name = "flatpak"
    build = "flatpak"
    static = ""
    toolchain_names = ["org.kde", "io.qt.qtwebengine"]
    compatible_hosts = ["debian", "fedora"]

    def __str__(self):
        return "flatpak"

    def get_env(self):
        env = super().get_env()
        env["FLATPAK_USER_DIR"] = self.buildEnv.build_dir
        return env
