import subprocess

from .base import PlatformInfo
from kiwixbuild.utils import which, pj
from kiwixbuild._global import neutralEnv


class Win32PlatformInfo(PlatformInfo):
    extra_libs = ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4', '-lmsvcr90', '-liphlpapi']
    arch_full = 'i686-w64-mingw32'
    def __init__(self, name, static):
        super().__init__(name, 'win32', static, [], ['fedora', 'debian'])

    def get_cross_config(self):
        return {
            'exec_wrapper_def': self.exec_wrapper_def,
            'binaries': self.binaries,
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

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

    @property
    def root_path(self):
        root_paths = {
            'fedora': '/usr/i686-w64-mingw32/sys-root/mingw',
            'debian': '/usr/i686-w64-mingw32'
        }
        return root_paths[neutralEnv('distname')]

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

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['LIBS'] = " ".join(self.extra_libs) + " " +env['LIBS']

Win32PlatformInfo('win32_dyn', False)
Win32PlatformInfo('win32_static', True)
