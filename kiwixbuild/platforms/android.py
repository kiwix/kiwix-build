from .base import PlatformInfo, MetaPlatformInfo
from kiwixbuild.utils import pj
from kiwixbuild._global import get_target_step, option


class AndroidPlatformInfo(PlatformInfo):
    build = 'android'
    static = True
    toolchain_names = ['android-ndk']
    compatible_hosts = ['fedora', 'debian']

    def __str__(self):
        return "android"

    def binaries(self, install_path):
        binaries = ((k,'{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'),
                             ('LD', 'ld'))
               )
        return {k:pj(install_path, 'bin', v)
                for k,v in binaries}

    @property
    def ndk_builder(self):
        return get_target_step('android-ndk', self.name)

    def get_cross_config(self):
        install_path = self.ndk_builder.install_path
        return {
            'exec_wrapper_def': '',
            'install_path': install_path,
            'binaries': self.binaries(install_path),
            'root_path': pj(install_path, 'sysroot'),
            'extra_libs': ['-llog'],
            'extra_cflags': [],
            'host_machine': {
                'system': 'Android',
                'lsystem': 'android',
                'cpu_family': self.arch,
                'cpu': self.cpu,
                'endian': 'little',
                'abi': self.abi
            },
        }

    def get_bin_dir(self):
        return [pj(self.ndk_builder.install_path, 'bin')]

    def set_env(self, env):
        root_path = pj(self.ndk_builder.install_path, 'sysroot')
        env['PKG_CONFIG_LIBDIR'] = pj(root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(root_path) + env['CFLAGS']
        env['CXXFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(root_path) + env['CXXFLAGS']
        env['LDFLAGS'] = '--sysroot={} '.format(root_path) + env['LDFLAGS']
        #env['CFLAGS'] = ' -fPIC -D_FILE_OFFSET_BITS=64 -O3 '+env['CFLAGS']
        #env['CXXFLAGS'] = (' -D__OPTIMIZE__ -fno-strict-aliasing '
        #                   ' -DU_HAVE_NL_LANGINFO_CODESET=0 '
        #                   '-DU_STATIC_IMPLEMENTATION -O3 '
        #                   '-DU_HAVE_STD_STRING -DU_TIMEZONE=0 ')+env['CXXFLAGS']
        env['NDK_DEBUG'] = '0'

    def set_compiler(self, env):
        binaries = self.binaries(self.ndk_builder.install_path)
        env['CC'] = binaries['CC']
        env['CXX'] = binaries['CXX']

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_android_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')


class AndroidArm(AndroidPlatformInfo):
    name = 'android_arm'
    arch = cpu = 'arm'
    arch_full = 'arm-linux-androideabi'
    abi = 'armeabi'

class AndroidArm(AndroidPlatformInfo):
    name = 'android_arm64'
    arch = 'arm64'
    arch_full = 'aarch64-linux-android'
    cpu = 'aarch64'
    abi = 'arm64-v8a'

class AndroidArm(AndroidPlatformInfo):
    name = 'android_mips'
    arch = abi = 'mips'
    arch_full = 'mipsel-linux-android'
    cpu = 'mipsel'

class AndroidArm(AndroidPlatformInfo):
    name = 'android_mips64'
    arch = abi = 'mips64'
    arch_full = 'mips64el-linux-android'
    cpu = 'mips64el'

class AndroidArm(AndroidPlatformInfo):
    name = 'android_x86'
    arch = abi = 'x86'
    arch_full = 'i686-linux-android'
    cpu = 'i686'

class AndroidArm(AndroidPlatformInfo):
    name = 'android_x86_64'
    arch = cpu = abi = 'x86_64'
    arch_full = 'x86_64-linux-android'

class Android(MetaPlatformInfo):
    name = "android"
    toolchain_names = ['android-sdk', 'gradle']
    compatible_hosts = ['fedora', 'debian']

    @property
    def subPlatformNames(self):
        return ['android_{}'.format(arch) for arch in option('android_arch')]

    def add_targets(self, targetName, targets):
        if targetName != 'kiwix-android':
            return super().add_targets(targetName, targets)
        else:
            return AndroidPlatformInfo.add_targets(self, targetName, targets)

    def __str__(self):
        return self.name

    @property
    def sdk_builder(self):
        return get_target_step('android-sdk', 'neutral')

    @property
    def gradle_builder(self):
        return get_target_step('gradle', 'neutral')

    def set_env(self, env):
        env['ANDROID_HOME'] = self.sdk_builder.install_path
        env['PATH'] = ':'.join([pj(self.gradle_builder.install_path, 'bin'), env['PATH']])
