from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class ZimTools(Dependency):
    name = "zim-tools"

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zim-tools.git"
        git_dir = "zim-tools"

    class Builder(MesonBuilder):
        dependencies = ['libzim']

        @property
        def configure_options(self):
            if self.buildEnv.platformInfo.static:
                yield "-Dstatic-linkage=true"
