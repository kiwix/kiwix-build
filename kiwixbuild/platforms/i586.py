
from .base import PlatformInfo


class I586PlatformInfo(PlatformInfo):
    arch_full = 'i586-linux-gnu'
    def __init__(self, name, static):
        super().__init__(name, 'i586', static, [], ['fedora', 'debian'])

    def get_cross_config(self):
        return {
            'binaries': self.binaries,
            'exec_wrapper_def': '',
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

    def set_env(self, env):
        env['CFLAGS'] = "-m32 -march=i586 -mno-sse "+env['CFLAGS']
        env['CXXFLAGS'] = "-m32 -march=i586 -mno-sse "+env['CXXFLAGS']
        env['LDFLAGS'] = "-m32 -march=i586 -mno-sse "+env['LDFLAGS']

    def get_bin_dir(self):
        return []


    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_i586_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

I586PlatformInfo('i586_dyn', False)
I586PlatformInfo('i586_static', True)
