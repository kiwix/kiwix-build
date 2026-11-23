from typing import ClassVar

from .base import ConfigInfo


class FlatpakConfigInfo(ConfigInfo):
    name = "flatpak"
    arch_name = "flatpak"
    build = "flatpak"
    static = ""
    toolchain_names: ClassVar[list[str]] = ["org.kde", "io.qt.qtwebengine"]
    compatible_hosts: ClassVar[list[str]] = ["debian", "ubuntu", "fedora"]

    def __str__(self):
        return "flatpak"

    def get_env(self):
        env = super().get_env()
        env["FLATPAK_USER_DIR"] = self.buildEnv.build_dir
        return env
