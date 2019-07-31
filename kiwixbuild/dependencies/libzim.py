from .base import (
    Dependency,
    GitClone,
    MesonBuilder)
from kiwixbuild._global import option

class Libzim(Dependency):
    name = "libzim"

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    class Builder(MesonBuilder):
        test_option = "-t 8"
        dependencies = ['zlib', 'lzma', 'xapian-core', 'icu4c']
        strip_option = ''

        @property
        def configure_option(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'android':
                return "-DUSE_BUFFER_HEADER=false"
            if platformInfo.build == 'iOS':
                return "-Db_bitcode=true"
            if platformInfo.name == 'native_mixed' and option('target') == 'libzim':
                return "-Dstatic-linkage=true"
            if platformInfo.name == "flatpak":
                return "--wrap-mode=nodownload"
            return ""
