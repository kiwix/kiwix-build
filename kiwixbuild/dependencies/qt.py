import shutil

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
    QMakeBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand


class Qt(Dependency):
    name = 'qt'

    class Source(ReleaseDownload):
        name = "qt"
        source_dir = "qt-5.10.1"
        archive = Remotefile('qt-everywhere-src-5.10.1.tar.xz',
                             '',
                             'http://ftp1.nluug.nl/languages/qt/archive/qt/5.10/5.10.1/single/qt-everywhere-src-5.10.1.tar.xz')

    class Builder(MakeBuilder):
        dependencies = ['icu4c', 'zlib']
        dynamic_configure_options = ["-shared"]
        static_configure_options = ["-static"]

        @property
        def all_configure_option(self):
            yield from self.configure_options
            if self.buildEnv.platformInfo.static:
                yield from self.static_configure_options
            else:
                yield from self.dynamic_configure_options
            if not self.target.force_native_build:
                yield from self.buildEnv.platformInfo.configure_options
            yield from ('-prefix', self.buildEnv.install_dir)
            yield from ('-libdir', pj(self.buildEnv.install_dir, self.buildEnv.libprefix))

        @property
        def configure_options(self):
            skip_modules = [
                'qt3d',
                'qtcanvas3d',
                'qtcharts',
                'qtconnectivity',
                'qtdatavis3d',
            #    'qtdeclarative',
                'qtdoc',
                'qtgamepad',
                'qtgraphicaleffects',
                'qtlocation',
                'qtmultimedia',
                'qtnetworkauth',
                'qtpurchasing',
            #    'qtquickcontrols',
                'qtquickcontrols2',
                'qtremoteobjects',
                'qtscript',
                'qtscxml',
                'qtsensors',
                'qtserialbus',
                'qtserialport',
                'qtspeech',
                'qtvirtualkeyboard',
                'qtwayland',
                'qtwebglplugin',
                'qtwebsockets',
#                'qtwebview',
            ]
            yield '-recheck'
            yield '-opensource'
            yield '-confirm-license'
            yield '-ccache'
            yield from ('-make', 'libs')
            for module in skip_modules:
               yield from ('-skip', module)


class QtWebEngine(Dependency):
    name = "qtwebengine"

    Source = Qt.Source

    class Builder(QMakeBuilder):
        dependencies = ['qt']
        subsource_dir = "qtwebengine"
