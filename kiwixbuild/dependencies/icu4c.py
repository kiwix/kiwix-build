from .base import (
    Dependency,
    SvnClone,
    MakeBuilder
)

from kiwixbuild.utils import SkipCommand
from kiwixbuild._global import get_target_step

class Icu(Dependency):
    name = "icu4c"

    class Source(SvnClone):
        name = "icu4c"
        svn_remote = "http://source.icu-project.org/repos/icu/tags/release-58-2/icu4c"
        svn_dir = "icu4c"

        patches = ["icu4c_fix_static_lib_name_mingw.patch",
                   "icu4c_android_elf64_st_info.patch",
                   "icu4c_custom_data.patch",
                   "icu4c_noxlocale.patch",
                   "icu4c_rpath.patch",
                   "icu4c_build_config.patch"]


    class Builder(MakeBuilder):
        subsource_dir = "source"

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
            if platformInfo.build == 'android':
                options += " --with-data-packaging=archive"
            return options
