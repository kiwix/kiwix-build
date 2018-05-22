import os
import subprocess

from .base_toolchain import Toolchain
from kiwixbuild.utils import which

pj = os.path.join

class mingw32_toolchain(Toolchain):
    name = 'mingw32'
    arch_full = 'i686-w64-mingw32'

    @property
    def root_path(self):
        return self.buildEnv.cross_config['root_path']

    @property
    def binaries(self):
        return {k:which('{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'))
               }

    @property
    def exec_wrapper_def(self):
        try:
            which('wine')
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exec_wrapper = 'wine'"

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v
