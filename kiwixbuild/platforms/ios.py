
from .base import PlatformInfo
import subprocess



class iOSPlatformInfo(PlatformInfo):
    __arch_infos = {
        'armv7': ('arm-apple-darwin', 'armv7', 'iphoneos'),
        'arm64': ('arm-apple-darwin', 'arm64', 'iphoneos'),
        'i386': ('', 'i386', 'iphonesimulator'),
        'x86_64': ('', 'x86_64', 'iphonesimulator'),
    }

    def __init__(self, name, arch):
        super().__init__(name, 'iOS', True, ['iOS_sdk'],
                         hosts=['Darwin'])
        self.arch = arch
        self.arch_full, self.cpu, self.sdk_name = self.__arch_infos[arch]
        self._root_path = None

    @property
    def root_path(self):
        if self._root_path is None:
            command = "xcodebuild -version -sdk {} | grep -E '^Path' | sed 's/Path: //'".format(self.sdk_name)
            self._root_path = subprocess.check_output(command, shell=True)[:-1].decode()
        return self._root_path

    def __str__(self):
        return "iOS"

    def get_cross_config(self, host):
        return {
            'extra_libs': ['-fembed-bitcode', '-isysroot', self.root_path, '-arch', self.arch, '-miphoneos-version-min=9.0', '-stdlib=libc++'],
            'extra_cflags': ['-fembed-bitcode', '-isysroot', self.root_path, '-arch', self.arch, '-miphoneos-version-min=9.0', '-stdlib=libc++'],
            'host_machine': {
                'system': 'Darwin',
                'lsystem': 'darwin',
                'cpu_family': self.arch,
                'cpu': self.cpu,
                'endian': '',
                'abi': ''
            },
        }

iOSPlatformInfo('iOS_armv7', 'armv7')
iOSPlatformInfo('iOS_arm64', 'arm64')
iOSPlatformInfo('iOS_i386', 'i386')
iOSPlatformInfo('iOS_x86_64', 'x86_64')
