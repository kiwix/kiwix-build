
from .base import PlatformInfo


class I586PlatformInfo(PlatformInfo):
    def __init__(self, name, static):
        super().__init__(name, 'i586', static, ['linux_i586_toolchain'], ['fedora', 'debian'])

    def get_cross_config(self):
        return {
            'extra_libs': ['-m32', '-march=i586', '-mno-sse'],
            'extra_cflags': ['-m32', '-march=i586', '-mno-sse'],
            'host_machine': {
                'system': 'linux',
                'lsystem': 'linux',
                'cpu_family': 'x86',
                'cpu': 'i586',
                'endian': 'little',
                'abi': ''
            }
        }


I586PlatformInfo('i586_dyn', False)
I586PlatformInfo('i586_static', True)
