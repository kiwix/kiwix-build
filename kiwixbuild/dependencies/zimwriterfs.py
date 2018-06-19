from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class Zimwriterfs(Dependency):
    name = "zimwriterfs"

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zimwriterfs.git"
        git_dir = "zimwriterfs"

    class Builder(MesonBuilder):
        dependencies = ['libzim', 'zlib', 'xapian-core', 'gumbo', 'icu4c', 'libmagic']

        @property
        def configure_options(self):
            yield "-Dmagic-install-prefix={}".format(self.buildEnv.install_dir)
            if self.buildEnv.platformInfo.static:
                yield "-Dstatic-linkage=true"
