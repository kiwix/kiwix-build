from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class ZimTools(Dependency):
    name = "zim-tools"
    dependencies = ['libzim']

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zim-tools.git"
        git_dir = "zim-tools"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
            if self.buildEnv.platform_info.static:
                return "-Dstatic-linkage=true"
            return ""
