from .base import (
    Dependency,
    GitClone,
    MesonBuilder)
from kiwixbuild._global import neutralEnv

class Kiwixlib(Dependency):
    name = "kiwix-lib"

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-lib.git"
        git_dir = "kiwix-lib"

    class Builder(MesonBuilder):
        @classmethod
        def get_dependencies(cls, platformInfo):
            base_dependencies = ["pugixml", "libzim", "zlib", "lzma", "libaria2"]
            if (platformInfo.build != 'android' and
                neutralEnv('distname') != 'Darwin'):
                base_dependencies += ['ctpp2c', 'ctpp2']
            if platformInfo.build != 'native':
                return base_dependencies + ["icu4c_cross-compile"]
            else:
                return base_dependencies + ["icu4c"]


        @property
        def configure_option(self):
            base_option = "-Dctpp2-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platformInfo.build == 'android':
                base_option += ' -Dandroid=true'
            return base_option

        @property
        def library_type(self):
            if self.buildEnv.platformInfo.build == 'android':
                return 'shared'
            return super().library_type
