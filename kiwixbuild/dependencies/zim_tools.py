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
        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            base_deps = ['libzim', 'docoptcpp', 'mustache']
            if platformInfo.build != 'win32':
                base_deps += ['libmagic', 'gumbo']
            return base_deps

        @property
        def configure_option(self):
            base_option  = ""
            # We don't build zimwriterfs on win32, and so we don't have magic
            if self.buildEnv.platformInfo.build != 'win32':
                base_option += " -Dmagic-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platformInfo.static:
                base_option += " -Dstatic-linkage=true"
            if self.buildEnv.platformInfo.build == 'iOS':
                base_option += " -Db_bitcode=true"
            return base_option
