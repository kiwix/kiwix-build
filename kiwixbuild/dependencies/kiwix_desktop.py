from .base import (
    Dependency,
    GitClone,
    QMakeBuilder)

class KiwixDesktop(Dependency):
    name = "kiwix-desktop"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-desktop.git"
        git_dir = "kiwix-desktop"
        git_ref = "appimage-hack"

    class Builder(QMakeBuilder):
        dependencies = ["qt", "qtwebengine", "libkiwix", "aria2"]
        make_install_target = 'install'
        configure_env = None

        flatpack_build_options = {
            "env": [
                "QMAKEPATH=/app/lib"
            ]
        }

        @property
        def configure_option(self):
            if self.buildEnv.platformInfo.name == 'flatpak':
                options = [
                    'QMAKE_INCDIR+=/app/include/QtWebEngine',
                    'QMAKE_INCDIR+=/app/include/QtWebEngineCore',
                    'QMAKE_INCDIR+=/app/include/QtWebEngineWidgets'
                ]
            else:
                options = ["PREFIX={}".format(self.buildEnv.install_dir)]
                if self.buildEnv.platformInfo.static:
                    options.append('"CONFIG+=static"')
            return " ".join(options)
