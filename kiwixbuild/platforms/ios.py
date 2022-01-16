import subprocess

from kiwixbuild._global import option
from kiwixbuild.utils import pj, xrun_find
from .base import PlatformInfo, MetaPlatformInfo, MixedMixin


class ApplePlatformInfo(PlatformInfo):
    build = 'iOS'
    static = True
    compatible_hosts = ['Darwin']
    arch = None
    host = None
    target = None
    sdk_name = None
    min_iphoneos_version = None
    min_macos_version = None

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
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_ios_cross_file.txt', 'cmake_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_ios_cross_file.txt', 'meson_cross_file.txt')

    def get_cross_config(self):
        config = {
            'root_path': self.root_path,
            'binaries': self.binaries,
            'exe_wrapper_def': '',
            'extra_libs': [
                '-isysroot', self.root_path,
                '-arch', self.arch,
                '-target',  self.target,
                '-stdlib=libc++'
            ],
            'extra_cflags': [
                '-isysroot', self.root_path,
                '-arch', self.arch,
                '-target', self.target,
                '-stdlib=libc++',
                *('-I{}'.format(include_dir) for include_dir in self.get_include_dirs())
            ],
            'host_machine': {
                'system': 'Darwin',
                'lsystem': 'darwin',
                'cpu_family': self.arch,
                'cpu': self.cpu,
                'endian': '',
                'abi': ''
            }
        }
        if self.min_iphoneos_version:
            config['extra_libs'].append('-miphoneos-version-min={}'.format(self.min_iphoneos_version))
            config['extra_cflags'].append('-miphoneos-version-min={}'.format(self.min_iphoneos_version))
        if self.min_macos_version:
            config['extra_libs'].append('-mmacosx-version-min={}'.format(self.min_macos_version))
            config['extra_cflags'].append('-mmacosx-version-min={}'.format(self.min_macos_version))
        return config

    def get_env(self):
        env = super().get_env()
        cflags = [env['CFLAGS']]
        if self.min_iphoneos_version:
            cflags.append('-miphoneos-version-min={}'.format(self.min_iphoneos_version))
        if self.min_macos_version:
            cflags.append('-mmacosx-version-min={}'.format(self.min_macos_version))
        env['CFLAGS'] = ' '.join(cflags)
        return env

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        cflags = [
            '-isysroot {}'.format(self.root_path),
            '-arch {}'.format(self.arch),
            '-target {}'.format(self.target),
            env['CFLAGS'],
        ]
        env['CC'] = 'clang'
        env['CXX'] = 'clang++'
        env['CFLAGS'] = ' '.join(cflags)
        env['CXXFLAGS'] = ' '.join([
            env['CFLAGS'],
            '-stdlib=libc++',
            '-std=c++11',
            env['CXXFLAGS'],
        ])
        env['LDFLAGS'] = ' '.join([
            ' -arch {}'.format(self.arch),
            '-isysroot {}'.format(self.root_path),
        ])

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
        return '--host={}'.format(self.host)


class iOSArm64(ApplePlatformInfo):
    name = 'iOS_arm64'
    arch = cpu = 'arm64'
    host = 'arm-apple-darwin'
    target = 'arm64-apple-ios'
    sdk_name = 'iphoneos'
    min_iphoneos_version = '15.0'


class iOSSimulatorX86(ApplePlatformInfo):
    """iOS / iPadOS simulator on Intel"""

    name = 'iOS_simulator_x86'
    arch = cpu = 'x86_64'
    host = 'x86_64-apple-darwin'
    target = 'x86_64-apple-ios'
    sdk_name = 'iphonesimulator'
    min_iphoneos_version = '15.0'


class iOSSimulatorArm64(ApplePlatformInfo):
    """iOS / iPadOS simulator on Apple Silicon"""

    name = 'iOS_simulator_arm64'
    arch = cpu = 'arm64'
    host = 'arm-apple-darwin'
    target = 'arm64-apple-ios-simulator'
    sdk_name = 'iphonesimulator'
    min_iphoneos_version = '15.0'


class macOSArm64(ApplePlatformInfo):
    """macOS on Apple Silicon"""

    name = 'macOS_arm64'
    arch = cpu = 'arm64'
    host = 'arm-apple-darwin'
    target = 'arm64-apple-macos'
    sdk_name = 'macosx'
    min_macos_version = '12.0'


class macOSX86(ApplePlatformInfo):
    """macOS on Intel"""

    name = 'macOS_x86'
    arch = cpu = 'x86_64'
    host = 'x86_64-apple-darwin'
    target = 'x86_64-apple-macos'
    sdk_name = 'macosx'
    min_macos_version = '12.0'


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
