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
        def get_dependencies(cls, platformInfo):
            base_dependencies = ['zlib', 'lzma', 'xapian-core']
            if platformInfo.build != 'native':
                return base_dependencies + ["icu4c_cross-compile"]
            else:
                return base_dependencies + ["icu4c"]
