from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class KiwixTools(Dependency):
    name = "kiwix-tools"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-tools.git"
        git_dir = "kiwix-tools"

    class Builder(MesonBuilder):
        dependencies = ["libkiwix"]

        @property
        def configure_options(self):
            if self.buildEnv.platformInfo.static:
                yield "-Dstatic-linkage=true"
