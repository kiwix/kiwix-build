from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder
)

from kiwixbuild.utils import SkipCommand, Remotefile
from kiwixbuild._global import get_target_step

class Icu(Dependency):
    name = "icu4c"

    class Source(ReleaseDownload):
        archive = Remotefile('icu4c-73_2-src.tgz',
                             '818a80712ed3caacd9b652305e01afc7fa167e6f2e94996da44b90c2ab604ce1',
                             'https://github.com/unicode-org/icu/releases/download/release-73-2/icu4c-73_2-src.tgz')
        patches = [
                   "icu4c_fix_static_lib_name_mingw.patch",
        #           "icu4c_android_elf64_st_info.patch",
        #           "icu4c_custom_data.patch",
        #           "icu4c_noxlocale.patch",
                   "icu4c_rpath.patch",
        #           "icu4c_build_config.patch",
                   "icu4c_wasm.patch"
                  ]


    class Builder(MakeBuilder):
        subsource_dir = "source"
        make_install_target = "install"

        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            plt = 'native_static' if platformInfo.static else 'native_dyn'
            return [(plt, 'icu4c')]

        @property
        def configure_option(self):
            options = ("--disable-samples --disable-tests --disable-extras "
                       "--disable-dyload --enable-rpath "
                       "--disable-icuio --disable-layoutex")
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build != 'native':
                icu_native_builder = get_target_step(
                    'icu4c',
                    'native_static' if platformInfo.static else 'native_dyn')
                options += " --with-cross-build={} --disable-tools".format(
                    icu_native_builder.build_path)
            if platformInfo.build in ('android', 'wasm'):
                options += " --with-data-packaging=archive"
            return options
