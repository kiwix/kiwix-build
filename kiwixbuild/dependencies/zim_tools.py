from kiwixbuild._global import neutral_env

from .base import Dependency, GitClone, MesonBuilder


class ZimTools(Dependency):
    name = "zim-tools"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zim-tools.git"
        git_dir = "zim-tools"

    class Builder(MesonBuilder):
        @classmethod
        def get_dependencies(cls, _config_info, _all_deps):
            base_deps = ["libzim", "docoptcpp", "mustache"]
            if neutral_env("distname") != "Windows":
                base_deps += ["libmagic", "gumbo"]
            return base_deps

        @property
        def configure_options(self):
            # We don't build zimwriterfs on Windows, and so we don't have magic
            if neutral_env("distname") != "Windows":
                yield f"-Dmagic-install-prefix={self.buildEnv.install_dir}"
            if self.buildEnv.configInfo.static:
                yield "-Dstatic-linkage=true"
