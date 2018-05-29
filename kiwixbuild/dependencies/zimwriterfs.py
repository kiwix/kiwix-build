from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class Zimwriterfs(Dependency):
    name = "zimwriterfs"

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zimwriterfs.git"
        git_dir = "zimwriterfs"
        release_git_ref = "1.1"

    class Builder(MesonBuilder):
        dependencies = ['libzim', 'zlib', 'xapian-core', 'gumbo', 'icu4c', 'libmagic']

        @property
        def configure_option(self):
            base_option = "-Dmagic-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platformInfo.static:
                base_option += " -Dstatic-linkage=true"
            return base_option
