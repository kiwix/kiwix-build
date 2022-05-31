from .base import PlatformInfo, _SCRIPT_DIR

from kiwixbuild.utils import pj
from kiwixbuild._global import get_target_step

from glob import glob
from os import makedirs, chmod, readlink, symlink
from os.path import basename, islink
from re import sub as subst
from shutil import copy2

def copy(src, dst, search=None, repl=None, mode=None):
    if islink(src):
        linkto = readlink(src)
        symlink(linkto, dst)
    else:
        if search is None:
            copy2(src, dst)
        else:
            with open(src, "r") as sources:
                lines = sources.readlines()
            with open(dst, "w") as sources:
                for line in lines:
                    sources.write(subst(search, repl, line))
    if mode is not None:
        chmod(dst, mode)


class MIPS32R2PlatformInfo(PlatformInfo):
    build = 'mips32r2_glibc_glibcxx'
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
        # apt-get'able debian/ubuntu hard-float glibc glibcxx toolchain
        return '/usr/mips-linux-gnu'

    @property
    def tcbindir(self):
        return pj(self.root_path, 'bin')

    @property
    def tcbinprefix(self):
        return '../../bin/' + self.arch_full + '-'

    @property
    def tclibdir(self):
        return pj(self.root_path, 'lib')

    @property
    def binaries(self):
        binaries = ((k,'{}{}'.format(self.tcbinprefix, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'),
                             ('LD', 'ld'))
               )
        return {k:pj(self.tcbindir, v)
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

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.tclibdir, 'pkgconfig')
        env['CFLAGS']   = " -march=mips32r2 -mtune=24kc "+env['CFLAGS']
        env['CXXFLAGS'] = " -march=mips32r2 -mtune=24kc "+env['CXXFLAGS']
        env['QEMU_LD_PREFIX'] = pj(self.root_path)
        env['QEMU_SET_ENV'] = "LD_LIBRARY_PATH={}".format(
            ':'.join([
                pj(self.tclibdir),
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
    name = MIPS32R2PlatformInfo.build + '_dyn'
    static = False

class MIPS32R2Static(MIPS32R2PlatformInfo):
    name = MIPS32R2PlatformInfo.build + '_static'
    static = True




class MIPS32R2_UC_GCXXPlatformInfo(MIPS32R2PlatformInfo):
    build = 'mips32r2_uclibc_glibcxx' # "shared, heterogeneous"
    arch_full = 'mips-linux-uclibc'

    @property
    def root_path(self):
        return '/dev/shm/freetz/toolchain/build/mips_gcc-5.5.0_uClibc-0.9.33.2-nptl/mips-linux-uclibc'

    @property
    def tcbinprefix(self):
        return self.arch_full + '-'

    def set_env(self, env):
        super().set_env(env)
        env['CFLAGS']   = " -msoft-float -Os -pipe -Wa,--trap "+env['CFLAGS']
        env['CXXFLAGS'] = " -msoft-float -Os -pipe -Wa,--trap "+env['CXXFLAGS']

class MIPS32R2_UC_GCXXDyn(MIPS32R2_UC_GCXXPlatformInfo):
    name = MIPS32R2_UC_GCXXPlatformInfo.build + '_dyn'
    static = False

    def finalize_setup(self):
        super().finalize_setup()
        d = pj(_SCRIPT_DIR, '..', '..', 'BUILD_'+self.name, 'INSTALL')

        makedirs(pj(d, 'bin'), mode=0o755, exist_ok=True)
        copy(pj(_SCRIPT_DIR, '..', 'patches', 'fixenv-nonstd-libdir'),
             pj(d, 'bin', 'fixenv-nonstd-libdir'),
             search=r'\$\{ARCH_FULL[^}]*\}',
             repl=self.arch_full,
             mode=0o755)

        d = pj(d, 'lib', self.arch_full)
        makedirs(d, mode=0o755, exist_ok=True)
        for f in glob(pj(self.tclibdir, 'libstdc++.so*')):
            copy(f, pj(d, basename(f)))

class MIPS32R2_UC_GCXXStatic(MIPS32R2_UC_GCXXPlatformInfo):
    name = MIPS32R2_UC_GCXXPlatformInfo.build + '_static'
    static = True




class MIPS32R2_UC_UCXXPlatformInfo(MIPS32R2_UC_GCXXPlatformInfo):
    build = 'mips32r2_uclibc_uclibcxx' # "pure, homogeneous"

    def get_cross_config(self):
        conf = super().get_cross_config()
        conf['extra_libs'] += [ '-lm' ]
        return conf

    @property
    def binaries(self):
        bins = super().binaries
        bins['CXX'] += '-uc'
        return bins

    def set_env(self, env):
        super().set_env(env)
        # for mips-linux-uclibc-g++-uc wrapper to find real binary
        env['PATH'] = ':'.join([pj(self.tcbindir), env['PATH']])

class MIPS32R2_UC_UCXXDyn(MIPS32R2_UC_UCXXPlatformInfo):
    name = MIPS32R2_UC_UCXXPlatformInfo.build + '_dyn'
    static = False

class MIPS32R2_UC_UCXXStatic(MIPS32R2_UC_UCXXPlatformInfo):
    name = MIPS32R2_UC_UCXXPlatformInfo.build + '_static'
    static = True
