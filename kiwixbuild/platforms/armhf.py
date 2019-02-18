from .base import PlatformInfo

from kiwixbuild.utils import pj
from kiwixbuild._global import get_target_step


class ArmhfPlatformInfo(PlatformInfo):
    build = 'armhf'
    arch_full = 'arm-linux-gnueabihf'
    toolchain_names = ['armhf']
    compatible_hosts = ['fedora', 'debian']

    def get_cross_config(self):
        return {
            'binaries': self.binaries,
            'exec_wrapper_def': '',
            'root_path': self.root_path,
            'extra_libs': [],
            'extra_cflags': ['-I{}'.format(pj(self.buildEnv.install_dir, 'include'))],
            'host_machine': {
                'system': 'linux',
                'lsystem': 'linux',
                'cpu_family': 'arm',
                'cpu': 'armhf',
                'endian': 'little',
                'abi': ''
            }
        }

    @property
    def tlc_source(self):
        return get_target_step('armhf', 'source')

    @property
    def root_path(self):
        return pj(self.tlc_source.source_path,
                  'arm-bcm2708',
                  'gcc-linaro-{}-raspbian-x64'.format(self.arch_full))

    @property
    def binaries(self):
        binaries = ((k,'{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'),
                             ('LD', 'ld'))
               )
        return {k:pj(self.root_path, 'bin', v)
                for k,v in binaries}

    @property
    def exec_wrapper_def(self):
        try:
            which('qemu-arm')
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exec_wrapper = 'qemu-arm'"

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = " -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CFLAGS']
        env['CXXFLAGS'] = " -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CXXFLAGS']
        env['QEMU_LD_PREFIX'] = pj(self.root_path, "arm-linux-gnueabihf", "libc")
        env['QEMU_SET_ENV'] = "LD_LIBRARY_PATH={}".format(
            ':'.join([
                pj(self.root_path, self.arch_full, "lib"),
                env['LD_LIBRARY_PATH']
        ]))

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

class ArmhfDyn(ArmhfPlatformInfo):
    name = 'armhf_dyn'
    static = False

class ArmhfStatic(ArmhfPlatformInfo):
    name = 'armhf_static'
    static = True
