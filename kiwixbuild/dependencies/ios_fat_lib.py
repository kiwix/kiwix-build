import os

from kiwixbuild.configs import ConfigInfo
from kiwixbuild.utils import copy_tree, run_command
from kiwixbuild._global import option
from .base import Dependency, NoopSource, Builder as BaseBuilder


class IOSFatLib(Dependency):
    name = "_ios_fat_lib"

    Source = NoopSource

    class Builder(BaseBuilder):
        @classmethod
        def get_dependencies(self, platfomInfo, alldeps):
            base_target = option("target")
            return [("iOS_{}".format(arch), base_target) for arch in option("ios_arch")]

        def _copy_headers(self, context):
            plt = ConfigInfo.get_config("iOS_{}".format(option("ios_arch")[0]))
            include_src = plt.buildEnv.install_dir / "include"
            include_dst = self.buildEnv.install_dir / "include"
            copy_tree(include_src, include_dst)

        def _merge_libs(self, context):
            lib_dirs = []
            for arch in option("ios_arch"):
                plt = ConfigInfo.get_config("iOS_{}".format(arch))
                lib_dirs.append(plt.buildEnv.install_dir / "lib")
            libs = []
            for f in lib_dirs[0].iterdir():
                if f.is_symlink():
                    continue
                if f.suffix in (".a", ".dylib"):
                    libs.append(f)
            (self.buildEnv.install_dir / "lib").mkdir(parents=True, exist_ok=True)
            for l in libs:
                command = [
                    "lipo",
                    "-create",
                    *[d / l for d in lib_dirs],
                    "-output",
                    self.buildEnv.install_dir / "lib" / l,
                ]
                run_command(command, self.buildEnv.install_dir, context)

        def build(self):
            self.command("copy_headers", self._copy_headers)
            self.command("merge_libs", self._merge_libs)
