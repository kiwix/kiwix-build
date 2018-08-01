from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class Libzim(Dependency):
    name = "libzim"

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    class Builder(MesonBuilder):
        test_option = "-t 8"
        dependencies = ['zlib', 'lzma', 'xapian-core', 'icu4c']

        @property
        def configure_option(self):
            options = ""
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'android':
                options += "-DUSE_BUFFER_HEADER=false"
            return options
