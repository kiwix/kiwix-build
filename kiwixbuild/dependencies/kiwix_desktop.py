from kiwixbuild._global import option
from .base import Dependency, GitClone, QMakeBuilder
import platform


class KiwixDesktop(Dependency):
    name = "kiwix-desktop"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-desktop.git"
        git_dir = "kiwix-desktop"

    class Builder(QMakeBuilder):
        dependencies = ["qt", "qtwebengine", "libkiwix", "aria2"]
        configure_env = None

        flatpack_build_options = {"env": {"QMAKEPATH": "/app"}}

        @property
        def make_targets(self):
            if platform.system() == "Windows":
                yield "release-all"
            else:
                yield from super().make_targets

        @property
        def make_install_targets(self):
            if platform.system() == "Windows":
                yield "release-install"
            else:
                yield "install"

        @property
        def configure_options(self):
            if self.buildEnv.configInfo.name != "flatpak":
                yield f"PREFIX={self.buildEnv.install_dir}"
            if self.buildEnv.configInfo.static:
                yield "CONFIG+=static"
