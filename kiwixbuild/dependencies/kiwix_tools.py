from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class KiwixTools(Dependency):
    name = "kiwix-tools"
    dependencies = ["kiwix-lib", "libmicrohttpd", "zlib"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-tools.git"
        git_dir = "kiwix-tools"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
            if self.buildEnv.platform_info.static:
                return "-Dstatic-linkage=true"
            return ""
