from .base import Dependency, ReleaseDownload, MakeBuilder

from kiwixbuild.utils import Remotefile, win_to_posix_path
from kiwixbuild._global import neutralEnv


class Xapian(Dependency):
    name = "xapian-core"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "xapian-core-1.4.23.tar.xz",
            "30d3518172084f310dab86d262b512718a7f9a13635aaa1a188e61dc26b2288c",
        )

    class Builder(MakeBuilder):
        @property
        def configure_options(self):
            if neutralEnv("distname") == "Windows":
                compile_script = win_to_posix_path(self.source_path / "compile")
                return [
                    f"CC={compile_script} cl -nologo",
                    f"CXX={compile_script} cl -nologo",
                    "CXXFLAGS=-EHsc",
                    "AR=lib",
                ]
            else:
                return [
                    "--disable-sse",
                    "--disable-backend-chert",
                    "--disable-backend-remote",
                    "--disable-documentation",
                ]

        def set_configure_env(self, env):
            lib_dir = self.buildEnv.install_dir / self.buildEnv.libprefix
            env["LDFLAGS"] = " ".join(
                [env["LDFLAGS"], "-L" + win_to_posix_path(lib_dir)]
            )

            include_dir = self.buildEnv.install_dir / "include"
            env["CXXFLAGS"] = " ".join(
                [env["CXXFLAGS"], "-O3", "-I" + win_to_posix_path(include_dir)]
            )

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
