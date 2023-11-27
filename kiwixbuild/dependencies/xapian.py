from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder, MesonBuilder
)

from kiwixbuild.utils import Remotefile
from kiwixbuild._global import neutralEnv


class Xapian(Dependency):
    name = "xapian-core"

    class Source(ReleaseDownload):
        src_archive = Remotefile(
            "xapian-core-1.4.23.tar.xz",
            "30d3518172084f310dab86d262b512718a7f9a13635aaa1a188e61dc26b2288c"
        )
        meson_patch = Remotefile(
            "xapian-core-1.4.23-1_patch.zip",
            "",
            "https://public.kymeria.fr/KIWIX/xapian-core-1.4.23-1_patch.zip"
        )
        archives = [src_archive, meson_patch]

#    class Builder(MakeBuilder):
#        configure_options = [
#            "--disable-sse",
#            "--disable-backend-chert",
#            "--disable-backend-remote",
#            "--disable-documentation"]
#        configure_env = {'_format_LDFLAGS': "{env.LDFLAGS} -L{buildEnv.install_dir}/{buildEnv.libprefix}",
#                         '_format_CXXFLAGS': "{env.CXXFLAGS} -I{buildEnv.install_dir}/include"}

    class Builder(MesonBuilder):
        configure_options = [
            "-Denable-sse=false",
            "-Denable-backend-chert=false",
            "-Denable-backend-remote=false"
        ]

        @classmethod
        def get_dependencies(cls, configInfo, allDeps):
            if neutralEnv("distname") == "Windows":
                return ["zlib"]
            deps = ["zlib", "lzma"]
            if (
                configInfo.build in ("win32", "wasm")
                or neutralEnv("distname") == "Darwin"
            ):
                return deps
            return deps + ["uuid"]
