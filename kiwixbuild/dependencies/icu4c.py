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
        archive = Remotefile('icu4c_svn_58-2.tar.gz',
                             'fd8fcc1f1b8b2b71b879e88844480ebec107189c21076c81573f71dca5686a0d')
        patches = ["icu4c_fix_static_lib_name_mingw.patch",
                   "icu4c_android_elf64_st_info.patch",
                   "icu4c_custom_data.patch",
                   "icu4c_noxlocale.patch",
                   "icu4c_rpath.patch",
                   "icu4c_build_config.patch",
                   "icu4c_run_tools_w_qemu_if_endianess_differs.patch"]


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
                options += " --with-cross-build={}".format(
                    icu_native_builder.build_path)
                if platformInfo.build == 'iOS':
                    options += " --disable-tools"
            if platformInfo.build == 'android':
                options += " --with-data-packaging=archive"
            return options
