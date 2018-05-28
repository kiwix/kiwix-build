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
        @classmethod
        def get_dependencies(cls, platformInfo):
            base_dependencies = ['libzim', 'zlib', 'xapian-core', 'gumbo']
            if platformInfo.build != 'native':
                return base_dependencies + ["icu4c_cross-compile", "libmagic_cross-compile"]
            else:
                return base_dependencies + ["icu4c", "libmagic"]

        @property
        def configure_option(self):
            base_option = "-Dmagic-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platformInfo.static:
                base_option += " -Dstatic-linkage=true"
            return base_option
