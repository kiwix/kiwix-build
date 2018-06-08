import os

from kiwixbuild.platforms import PlatformInfo
from kiwixbuild.utils import pj, copy_tree, run_command
from kiwixbuild._global import option
from .base import (
    Dependency,
    NoopSource,
    Builder as BaseBuilder)



class IOSFatLib(Dependency):
    name = "_ios_fat_lib"

    Source = NoopSource

    class Builder(BaseBuilder):

        @classmethod
        def get_dependencies(self, platfomInfo, alldeps):
            base_target = option('target')
            return [('iOS_{}'.format(arch), base_target) for arch in option('ios_arch')]

        def _copy_headers(self, context):
            plt = PlatformInfo.get_platform('iOS_{}'.format(option('ios_arch')[0]))
            include_src = pj(plt.buildEnv.install_dir, 'include')
            include_dst = pj(self.buildEnv.install_dir, 'include')
            copy_tree(include_src, include_dst)

        def _merge_libs(self, context):
            lib_dirs = []
            for arch in option('ios_arch'):
                plt = PlatformInfo.get_platform('iOS_{}'.format(arch))
                lib_dirs.append(pj(plt.buildEnv.install_dir, 'lib'))
            libs = []
            for f in os.listdir(lib_dirs[0]):
                if os.path.islink(pj(lib_dirs[0], f)):
                    continue
                if f.endswith('.a') or f.endswith('.dylib'):
                    libs.append(f)
            os.makedirs(pj(self.buildEnv.install_dir, 'lib'), exist_ok=True)
            command_tmp = "lipo -create {input} -output {output}"
            for l in libs:
                command = command_tmp.format(
                    input=" ".join(pj(d, l) for d in lib_dirs),
                    output=pj(self.buildEnv.install_dir, 'lib', l))
                run_command(command, self.buildEnv.install_dir, context)

        def build(self):
            self.command('copy_headers', self._copy_headers)
            self.command('merge_libs', self._merge_libs)
