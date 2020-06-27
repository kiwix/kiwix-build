from .base import (
    Dependency,
    GitClone,
    MesonBuilder)

class ZimTools(Dependency):
    name = "zim-tools"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zim-tools.git"
        git_dir = "zim-tools"

    class Builder(MesonBuilder):
        dependencies = ['libzim', 'docoptcpp']

        @property
        def configure_option(self):
            base_option  = ""
            if self.buildEnv.platformInfo.build not in ('android', 'win32'):
                base_option += " -Dmagic-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platformInfo.static:
                base_option += " -Dstatic-linkage=true"
            return base_option
