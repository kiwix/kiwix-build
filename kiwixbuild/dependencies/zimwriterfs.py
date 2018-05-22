from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class Zimwriterfs(Dependency):
    name = "zimwriterfs"

    @property
    def dependencies(self):
        base_dependencies = ['libzim', 'zlib', 'xapian-core', 'gumbo']
        if self.buildEnv.platform_info.build != 'native':
            return base_dependencies + ["icu4c_cross-compile", "libmagic_cross-compile"]
        else:
            return base_dependencies + ["icu4c", "libmagic"]

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zimwriterfs.git"
        git_dir = "zimwriterfs"
        release_git_ref = "1.1"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
            base_option = "-Dmagic-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platform_info.static:
                base_option += " -Dstatic-linkage=true"
            return base_option
