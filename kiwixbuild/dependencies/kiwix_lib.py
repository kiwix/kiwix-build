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
        dependencies = ["pugixml", "libzim", "zlib", "lzma", "libcurl", "icu4c", "mustache"]

        @property
        def configure_option(self):
            if self.buildEnv.platformInfo.build == 'android':
                return '-Dandroid=true'
            if self.buildEnv.platformInfo.build == 'iOS':
                return '-Db_bitcode=true'
            return ''

        @property
        def library_type(self):
            if self.buildEnv.platformInfo.build == 'android':
                return 'shared'
            return super().library_type
