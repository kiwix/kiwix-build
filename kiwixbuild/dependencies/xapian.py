from .base import Dependency, GitClone, ReleaseDownload, MakeBuilder, MesonBuilder
from kiwixbuild.utils import Remotefile
from kiwixbuild._global import neutralEnv
import platform


class Xapian(Dependency):
    name = "xapian-core"
    version = "1.4.26"  

    if platform.system() == "Windows":

        class Source(GitClone):
            git_remote = "https://github.com/openzim/xapian-meson.git"
            git_dir = "xapian-core"

        class Builder(MesonBuilder):
            configure_options = [
                "-Denable-sse=false",
                "-Denable-backend-chert=false",
                "-Denable-backend-remote=false",
            ]
            subsource_dir = "xapian-core"

            @classmethod
            def get_dependencies(cls, configInfo, allDeps):
                return ["zlib"]

    else:

        class Source(ReleaseDownload):
            archive = Remotefile(
                f"xapian-core-{Xapian.version}.tar.xz",  
                "30d3518172084f310dab86d262b512718a7f9a13635aaa1a188e61dc26b2288c",
                f"https://oligarchy.co.uk/xapian/{Xapian.version}/xapian-core-{Xapian.version}.tar.xz",  
                )

        class Builder(MakeBuilder):
            configure_options = [
                "--disable-sse",
                "--disable-backend-chert",
                "--disable-backend-remote",
                "--disable-documentation",
            ]
            configure_env = {
                "_format_LDFLAGS": "{env.LDFLAGS} -L{buildEnv.install_dir}/{buildEnv.libprefix}",
                "_format_CXXFLAGS": "{env.CXXFLAGS} -I{buildEnv.install_dir}/include",
            }

            @classmethod
            def get_dependencies(cls, configInfo, allDeps):
                deps = ["zlib", "lzma"]
                if configInfo.build == "wasm" or neutralEnv("distname") == "Darwin":
                    return deps
                return deps + ["uuid"]
