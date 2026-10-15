import platform
from typing import ClassVar

from kiwixbuild._global import neutral_env
from kiwixbuild.utils import Remotefile

from .base import Dependency, GitClone, MakeBuilder, MesonBuilder, ReleaseDownload


class Xapian(Dependency):
    name = "xapian-core"

    if platform.system() == "Windows":

        class Source(GitClone):
            git_remote = "https://github.com/openzim/xapian-meson.git"
            git_dir = "xapian-core"

        class Builder(MesonBuilder):
            configure_options: ClassVar[list[str]] = [
                "-Denable-sse=false",
                "-Denable-backend-chert=false",
                "-Denable-backend-remote=false",
            ]
            subsource_dir = "xapian-core"

            @classmethod
            def get_dependencies(cls, _config_info, _all_deps):
                return ["zlib"]

    else:

        class Source(ReleaseDownload):
            archive = Remotefile(
                "xapian-core-1.4.23.tar.xz",
                "30d3518172084f310dab86d262b512718a7f9a13635aaa1a188e61dc26b2288c",
            )

        class Builder(MakeBuilder):
            configure_options: ClassVar[list[str]] = [
                "--disable-sse",
                "--disable-backend-chert",
                "--disable-backend-remote",
                "--disable-documentation",
            ]
            configure_env: ClassVar[dict[str, str]] = {
                "_format_LDFLAGS": "{env.LDFLAGS} -L{buildEnv.install_dir}/{buildEnv.libprefix}",
                "_format_CXXFLAGS": "{env.CXXFLAGS} -O3 -I{buildEnv.install_dir}/include",
            }

            @classmethod
            def get_dependencies(cls, config_info, _all_deps):
                deps = ["zlib", "lzma"]
                if config_info.build == "wasm" or neutral_env("distname") == "Darwin":
                    return deps
                return [*deps, "uuid"]
