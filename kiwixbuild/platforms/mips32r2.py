from .base import PlatformInfo

from kiwixbuild.utils import pj
from kiwixbuild._global import get_target_step


class MIPS32R2PlatformInfo(PlatformInfo):
    build = 'mips'
    arch_full = 'mips-linux-gnu'
    compatible_hosts = ['fedora', 'debian']

    def get_cross_config(self):
        return {
            'binaries': self.binaries,
            'exec_wrapper_def': '',
            'root_path': self.root_path,
            'extra_libs': [],
            'extra_cflags': [],
            'host_machine': {
                'system': 'linux',
                'lsystem': 'linux',
                'cpu_family': 'mips32r2',
                'cpu': '24kc',
                'endian': 'big',
                'abi': ''
            }
        }

    @property
    def root_path(self):
        return '/usr/mips-linux-gnu'

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
        return {k:pj('/usr', 'bin', v)
                for k,v in binaries}

    @property
    def exec_wrapper_def(self):
        try:
            which('qemu-mips-static')
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exec_wrapper = 'qemu-mips-static'"

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        # soft float is another abi and thus unsupported by current maintained (apt-get'able) debian/ubuntu tcs,
        # additionally these are (gnu) libc only; if uclibc is needed, see https://buildroot.org/downloads/ and
        # make a toolchain and rootfs, then checkout and use kiwixbuild --target_platform native_* within chroot env
        # (it needs qemu-mips-static from host copied to rootfs/usr/bin, in order to chroot into using a non-mips-host)
        #env['CFLAGS'] = " -march=mips32r2 -mtune=24kc -msoft-float "+env['CFLAGS']
        #env['CXXFLAGS'] = " -march=mips32r2 -mtune=24kc -msoft-float "+env['CXXFLAGS']
        env['CFLAGS'] = " -march=mips32r2 -mtune=24kc "+env['CFLAGS']
        env['CXXFLAGS'] = " -march=mips32r2 -mtune=24kc "+env['CXXFLAGS']
        env['QEMU_LD_PREFIX'] = pj(self.root_path)
        env['QEMU_SET_ENV'] = "LD_LIBRARY_PATH={}".format(
            ':'.join([
                pj(self.root_path, "lib"),
                env['LD_LIBRARY_PATH']
        ]))

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

class MIPS32R2Dyn(MIPS32R2PlatformInfo):
    name = 'mips32r2_dyn'
    static = False

class MIPS32R2Static(MIPS32R2PlatformInfo):
    name = 'mips32r2_static'
    static = True
