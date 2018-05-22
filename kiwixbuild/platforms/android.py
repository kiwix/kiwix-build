from .base import PlatformInfo


class AndroidPlatformInfo(PlatformInfo):
    __arch_infos = {
        'arm' : ('arm-linux-androideabi', 'arm', 'armeabi'),
        'arm64': ('aarch64-linux-android', 'aarch64', 'arm64-v8a'),
        'mips': ('mipsel-linux-android', 'mipsel', 'mips'),
        'mips64': ('mips64el-linux-android', 'mips64el', 'mips64'),
        'x86': ('i686-linux-android', 'i686', 'x86'),
        'x86_64': ('x86_64-linux-android', 'x86_64', 'x86_64'),
    }

    def __init__(self, name, arch):
        super().__init__(name, 'android', True, ['android_ndk', 'android_sdk'],
                         hosts=['fedora', 'debian'])
        self.arch = arch
        self.arch_full, self.cpu, self.abi = self.__arch_infos[arch]

    def __str__(self):
        return "android"

    def get_cross_config(self):
        return {
            'extra_libs': [],
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



AndroidPlatformInfo('android_arm', 'arm')
AndroidPlatformInfo('android_arm64', 'arm64')
AndroidPlatformInfo('android_mips', 'mips')
AndroidPlatformInfo('android_mips64', 'mips64')
AndroidPlatformInfo('android_x86', 'x86')
AndroidPlatformInfo('android_x86_64', 'x86_64')
