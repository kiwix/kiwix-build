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
        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            core_dependencies = ['xapian-core']
            if (platformInfo.build == 'flatpak'):
                return core_dependencies
            dependencies = core_dependencies + ['zlib', 'lzma', 'icu4c']
            return dependencies

        @property
        def configure_option(self):
            options = ""
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'android':
                options += "-DUSE_BUFFER_HEADER=false"
            return options
