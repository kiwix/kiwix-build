from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class Kiwixlib(Dependency):
    name = "kiwix-lib"

    @property
    def dependencies(self):
        base_dependencies = ["pugixml", "libzim", "zlib", "lzma", "libaria2"]
        if ( self.buildEnv.platform_info.build != 'android'
          and self.buildEnv.distname != 'Darwin'):
            base_dependencies += ['ctpp2c', 'ctpp2']
        if self.buildEnv.platform_info.build != 'native':
            return base_dependencies + ["icu4c_cross-compile"]
        else:
            return base_dependencies + ["icu4c"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-lib.git"
        git_dir = "kiwix-lib"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
            base_option = "-Dctpp2-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platform_info.build == 'android':
                base_option += ' -Dandroid=true'
            return base_option

        @property
        def library_type(self):
            if self.buildEnv.platform_info.build == 'android':
                return 'shared'
            return super().library_type
