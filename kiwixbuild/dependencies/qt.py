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
                             'http://ftp.oregonstate.edu/.1/blfs/conglomeration/qt5/qt-everywhere-src-5.10.1.tar.xz')

    class Builder(MakeBuilder):
        dependencies = ['icu4c', 'zlib']
        configure_option_template = "{dep_options} {static_option} {env_option} -prefix {install_dir} -libdir {libdir}"
        dynamic_configure_option = "-shared"
        static_configure_option = "-static"

        @property
        def configure_option(self):
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
            skip_modules = " ".join("-skip {}".format(m) for m in skip_modules)
            options = "-recheck -opensource -confirm-license -ccache -make libs {}".format(skip_modules)
            return options

class QtWebEngine(Dependency):
    name = "qtwebengine"

    Source = Qt.Source

    class Builder(QMakeBuilder):
        dependencies = ['qt']
        subsource_dir = "qtwebengine"
