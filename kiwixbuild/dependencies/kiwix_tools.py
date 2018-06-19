from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class KiwixTools(Dependency):
    name = "kiwix-tools"

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-tools.git"
        git_dir = "kiwix-tools"

    class Builder(MesonBuilder):
        dependencies = ["kiwix-lib", "libmicrohttpd", "zlib"]

        @property
        def configure_options(self):
            if self.buildEnv.platformInfo.static:
                yield "-Dstatic-linkage=true"
