from .base import Dependency, GitClone, QMakeBuilder


class KiwixDesktop(Dependency):
    name = "kiwix-desktop"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-desktop.git"
        git_dir = "kiwix-desktop"

    class Builder(QMakeBuilder):
        dependencies = ["qt", "qtwebengine", "libkiwix", "aria2"]
        make_install_targets = ["install"]
        configure_env = None

        flatpack_build_options = {"env": ["QMAKEPATH=/app/lib"]}

        @property
        def configure_options(self):
            if self.buildEnv.platformInfo.name == "flatpak":
                yield "QMAKE_INCDIR+=/app/include/QtWebEngine"
                yield "QMAKE_INCDIR+=/app/include/QtWebEngineCore"
                yield "QMAKE_INCDIR+=/app/include/QtWebEngineWidgets"
            else:
                yield f"PREFIX={self.buildEnv.install_dir}"
            if self.buildEnv.platformInfo.static:
                yield "CONFIG+=static"
