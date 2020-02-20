
import subprocess

from .base import PlatformInfo, MetaPlatformInfo
from kiwixbuild.utils import pj, xrun_find
from kiwixbuild._global import option

class iOSPlatformInfo(PlatformInfo):
    build = 'iOS'
    static = True
    compatible_hosts = ['Darwin']
    min_iphoneos_version = '9.0'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._root_path = None

    @property
    def root_path(self):
        if self._root_path is None:
            command = "xcrun --sdk {} --show-sdk-path".format(self.sdk_name)
            self._root_path = subprocess.check_output(command, shell=True)[:-1].decode()
        return self._root_path

    def __str__(self):
        return "iOS"

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_ios_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

    def get_cross_config(self):
        return {
            'root_path': self.root_path,
            'binaries': self.binaries,
            'exe_wrapper_def': '',
            'extra_libs': ['-fembed-bitcode', '-isysroot', self.root_path, '-arch', self.arch, '-miphoneos-version-min={}'.format(self.min_iphoneos_version), '-stdlib=libc++'],
            'extra_cflags': ['-fembed-bitcode', '-isysroot', self.root_path, '-arch', self.arch, '-miphoneos-version-min={}'.format(self.min_iphoneos_version), '-stdlib=libc++', '-I{}'.format(pj(self.buildEnv.install_dir, 'include'))],
            'host_machine': {
                'system': 'Darwin',
                'lsystem': 'darwin',
                'cpu_family': self.arch,
                'cpu': self.cpu,
                'endian': '',
                'abi': ''
            }
        }

    def get_env(self):
        env = super().get_env()
        env['MACOSX_DEPLOYMENT_TARGET'] = '10.10'
        return env

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        env['CFLAGS'] = " -fembed-bitcode -isysroot {SDKROOT} -arch {arch} -miphoneos-version-min={min_iphoneos_version} ".format(SDKROOT=self.root_path, min_iphoneos_version=self.min_iphoneos_version, arch=self.arch) + env['CFLAGS']
        env['CXXFLAGS'] = env['CFLAGS'] + " -stdlib=libc++ -std=c++11 "+env['CXXFLAGS']
        env['LDFLAGS'] = " -arch {arch} -isysroot {SDKROOT} ".format(SDKROOT=self.root_path, arch=self.arch)


    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    @property
    def binaries(self):
        return {
            'CC': xrun_find('clang'),
            'CXX': xrun_find('clang++'),
            'AR': xrun_find('ar'),
            'STRIP': xrun_find('strip'),
            'RANLIB': xrun_find('ranlib'),
            'LD': xrun_find('ld'),
            'PKGCONFIG': 'pkg-config',
        }

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

class iOSArmv7(iOSPlatformInfo):
    name = 'iOS_armv7'
    arch = cpu = 'armv7'
    arch_full =  'armv7-apple-darwin'
    sdk_name = 'iphoneos'

class iOSArm64(iOSPlatformInfo):
    name = 'iOS_arm64'
    arch = cpu = 'arm64'
    arch_full =  'arm-apple-darwin'
    sdk_name = 'iphoneos'

class iOSi386(iOSPlatformInfo):
    name = 'iOS_i386'
    arch = cpu = 'i386'
    arch_full =  'i386-apple-darwin'
    sdk_name = 'iphonesimulator'

class iOSx64(iOSPlatformInfo):
    name = 'iOS_x86_64'
    arch = cpu = 'x86_64'
    arch_full =  'x86_64-apple-darwin'
    sdk_name = 'iphonesimulator'

class IOS(MetaPlatformInfo):
    name = "iOS_multi"
    compatible_hosts = ['Darwin']

    @property
    def subPlatformNames(self):
        return ['iOS_{}'.format(arch) for arch in option('ios_arch')]

    def add_targets(self, targetName, targets):
        super().add_targets(targetName, targets)
        return PlatformInfo.add_targets(self, '_ios_fat_lib', targets)

    def __str__(self):
        return self.name
