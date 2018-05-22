from .base_toolchain import Toolchain

from kiwixbuild.utils import pj, xrun_find

class iOS_sdk(Toolchain):
    @property
    def binaries(self):
        return {
            'CC': xrun_find('clang'),
            'CXX': xrun_find('clang++'),
            'AR': '/usr/bin/ar',
            'STRIP': '/usr/bin/strip',
            'RANLIB': '/usr/bin/ranlib',
            'LD': '/usr/bin/ld',
        }

    @property
    def configure_option(self):
        return '--host=arm-apple-darwin'

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']
