from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class Libzim(Dependency):
    name = "libzim"

    @property
    def dependencies(self):
        base_dependencies = ['zlib', 'lzma', 'xapian-core']
        if self.buildEnv.platform_info.build != 'native':
            return base_dependencies + ["icu4c_cross-compile"]
        else:
            return base_dependencies + ["icu4c"]

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    class Builder(MesonBuilder):
        test_option = "-t 8"
