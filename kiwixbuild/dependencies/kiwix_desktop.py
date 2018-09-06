from .base import (
    Dependency,
    GitClone,
    QMakeBuilder)

class KiwixDesktop(Dependency):
    name = "kiwix-desktop"

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-desktop.git"
        git_dir = "kiwix-desktop"

    class Builder(QMakeBuilder):
        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            core_dependencies = ["kiwix-lib"]
            if (platformInfo.build == 'flatpak'):
                return core_dependencies
            dependencies = core_dependencies + ["qt", "qtwebengine"]
            return dependencies

        @property
        def configure_option(self):
            options = ["PREFIX={}".format(self.buildEnv.install_dir)]
            if self.buildEnv.platformInfo.static:
                options.append('"CONFIG+=static"')
            return " ".join(options)
