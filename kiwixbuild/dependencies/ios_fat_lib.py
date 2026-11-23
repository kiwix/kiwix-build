import os

from kiwixbuild._global import option
from kiwixbuild.configs import ConfigInfo
from kiwixbuild.utils import copy_tree, pj, run_command

from .base import Builder as BaseBuilder
from .base import Dependency, NoopSource


class IOSFatLib(Dependency):
    name = "_ios_fat_lib"

    Source = NoopSource

    class Builder(BaseBuilder):
        @classmethod
        def get_dependencies(cls, _config_info, _all_deps):
            base_target = option("target")
            return [(f"ios_{arch}", base_target) for arch in option("ios_arch")]

        def _copy_headers(self, context):  # noqa: ARG002 (passed by keyword)
            plt = ConfigInfo.get_config("ios_{}".format(option("ios_arch")[0]))
            include_src = pj(plt.buildEnv.install_dir, "include")
            include_dst = pj(self.buildEnv.install_dir, "include")
            copy_tree(include_src, include_dst)

        def _merge_libs(self, context):
            lib_dirs = []
            for arch in option("ios_arch"):
                plt = ConfigInfo.get_config(f"ios_{arch}")
                lib_dirs.append(pj(plt.buildEnv.install_dir, "lib"))
            libs = []
            for f in os.listdir(lib_dirs[0]):
                if os.path.islink(pj(lib_dirs[0], f)):
                    continue
                if f.endswith(".a") or f.endswith(".dylib"):
                    libs.append(f)
            os.makedirs(pj(self.buildEnv.install_dir, "lib"), exist_ok=True)
            for lib in libs:
                command = [
                    "lipo",
                    "-create",
                    *[pj(d, lib) for d in lib_dirs],
                    "-output",
                    pj(self.buildEnv.install_dir, "lib", lib),
                ]
                run_command(command, self.buildEnv.install_dir, context)

        def build(self):
            self.command("copy_headers", self._copy_headers)
            self.command("merge_libs", self._merge_libs)
