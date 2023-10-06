from .base import PlatformInfo, MixedMixin

from kiwixbuild.utils import pj
from kiwixbuild._global import get_target_step


class MuslPlatformInfo(PlatformInfo):
    compatible_hosts = ['fedora', 'debian']

    def get_cross_config(self):
        return {
            'binaries': self.binaries,
            'exe_wrapper_def': '',
            'root_path': self.root_path,
            'extra_libs': [],
            'extra_cflags': ['-I{}'.format(include_dir) for include_dir in self.get_include_dirs()],
            'host_machine': {
                'system': 'linux',
                'lsystem': 'linux',
                'cpu_family': self.cpu_family,
                'cpu': self.cpu,
                'endian': 'little',
                'abi': ''
            }
        }

    @property
    def tlc_source(self):
        return get_target_step(self.build, 'source')

    @property
    def root_path(self):
        return self.tlc_source.source_path

    @property
    def binaries(self):
        binaries = ((k,'{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'),
                             ('LD', 'ld'),
                             ('LDSHARED', 'g++ -shared')
                             )
               )
        binaries = {k:pj(self.root_path, 'bin', v)
                    for k,v in binaries}
        binaries['PKGCONFIG'] = 'pkg-config'
        return binaries

    @property
    def exe_wrapper_def(self):
        try:
            which(self.qemu)
        except subprocess.CalledProcessError:
            return ""
        except AttributeError:
            return ""
        else:
            return f"exe_wrapper = '{self.qemu}'"

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def get_env(self):
        env = super().get_env()
        env['LD_LIBRARY_PATH'] = ':'.join([
            pj(self.root_path, self.arch_full, 'lib64'),
            pj(self.root_path, 'lib'),
            env['LD_LIBRARY_PATH']
        ])
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['QEMU_LD_PREFIX'] = pj(self.root_path, self.arch_full, "libc")
        env['QEMU_SET_ENV'] = "LD_LIBRARY_PATH={}".format(
            ':'.join([
                pj(self.root_path, self.arch_full, "lib"),
                env['LD_LIBRARY_PATH']
        ]))
        return env

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        env['LD_LIBRARY_PATH'] = ':'.join([
            pj(self.root_path, self.arch_full, 'lib'),
            env['LD_LIBRARY_PATH']
        ])
        env['CFLAGS'] = " -fPIC -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CFLAGS']
        env['CXXFLAGS'] = " -fPIC -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CXXFLAGS']

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')


class Aarch64MuslPlatformInfo(MuslPlatformInfo):
    build = 'aarch64_musl'
    arch_full = 'aarch64-linux-musl'
    toolchain_names = ['aarch64_musl']
    libdir = "lib/aarch64-linux-musl"
    cpu_family = 'arm'
    cpu = 'armhf'
    qemu = 'qemu-arm'


class Aarch64MuslDyn(Aarch64MuslPlatformInfo):
    name = 'aarch64_musl_dyn'
    static = False

class Aarch64MuslStatic(Aarch64MuslPlatformInfo):
    name = 'aarch64_musl_static'
    static = True

class Aarch64MuslMixed(MixedMixin('aarch64_musl_static'), Aarch64MuslPlatformInfo):
    name = 'aarch64_musl_mixed'
    static = False


class X86_64MuslPlatformInfo(MuslPlatformInfo):
    build = 'x86-64_musl'
    arch_full = 'x86_64-linux-musl'
    toolchain_names = ['x86-64_musl']
    libdir = "lib/x86_64-linux-musl"
    cpu_family = 'x86_64'
    cpu = 'x86_64'


class X86_64MuslDyn(X86_64MuslPlatformInfo):
    name = 'x86-64_musl_dyn'
    static = False

class X86_64MuslStatic(X86_64MuslPlatformInfo):
    name = 'x86-64_musl_static'
    static = True

class x86_64MuslMixed(MixedMixin('x86-64_musl_static'), X86_64MuslPlatformInfo):
    name = 'x86-64_musl_mixed'
    static = False
