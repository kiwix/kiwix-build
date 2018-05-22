from .base import PlatformInfo


class Win32PlatformInfo(PlatformInfo):
    def __init__(self, name, static):
        super().__init__(name, 'win32', static, ['mingw32_toolchain'], ['fedora', 'debian'])
        self.extra_libs = ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4', '-lmsvcr90', '-liphlpapi']

    def get_cross_config(self, host):
        root_paths = {
            'fedora': '/usr/i686-w64-mingw32/sys-root/mingw',
            'debian': '/usr/i686-w64-mingw32'
        }
        self.root_path = root_paths[host]
        return {
            'root_path': self.root_path,
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

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['LIBS'] = " ".join(self.extra_libs) + " " +env['LIBS']

Win32PlatformInfo('win32_dyn', False)
Win32PlatformInfo('win32_static', True)
