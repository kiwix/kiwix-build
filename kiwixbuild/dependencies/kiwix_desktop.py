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
        dependencies = ["qt", "qtwebengine", "kiwix-lib", "aria2"]
        make_install_target = 'install'

        @property
        def configure_option(self):
            if self.buildEnv.platformInfo.name == 'flatpak':
                return []
            options = ["PREFIX={}".format(self.buildEnv.install_dir)]
            if self.buildEnv.platformInfo.static:
                options.append('"CONFIG+=static"')
            return " ".join(options)
