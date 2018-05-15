import os
import subprocess

from .base_toolchain import Toolchain
from kiwixbuild.dependencies import GitClone
from kiwixbuild.utils import Remotefile, which
pj = os.path.join

class linux_i586_toolchain(Toolchain):
    name = 'linux_i586'
    arch_full = 'i586-linux-gnu'

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    @property
    def binaries(self):
        return {k:which(v)
               for k, v in (('CC', os.environ.get('CC', 'gcc')),
                             ('CXX', os.environ.get('CXX', 'g++')),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('RANLIB', 'ranlib'),
                             ('LD', 'ld'))
               }

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def set_env(self, env):
        env['CFLAGS'] = "-m32 -march=i586 -mno-sse "+env['CFLAGS']
        env['CXXFLAGS'] = "-m32 -march=i586 -mno-sse "+env['CXXFLAGS']
        env['LDFLAGS'] = "-m32 -march=i586 -mno-sse "+env['LDFLAGS']

    def get_bin_dir(self):
        return []
