from .base import PlatformInfo


class Win32PlatformInfo(PlatformInfo):
    extra_libs = ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4', '-lmsvcr90', '-liphlpapi']
    def __init__(self, name, static):
        super().__init__(name, 'win32', static, ['mingw32_toolchain'], ['fedora', 'debian'])

    def get_cross_config(self):
        return {
            'extra_libs': self.extra_libs,
            'extra_cflags': ['-DWIN32'],
            'host_machine': {
                'system': 'Windows',
                'lsystem': 'windows',
                'cpu_family': 'x86',
                'cpu': 'i686',
                'endian': 'little',
                'abi': ''
            }
        }

Win32PlatformInfo('win32_dyn', False)
Win32PlatformInfo('win32_static', True)
