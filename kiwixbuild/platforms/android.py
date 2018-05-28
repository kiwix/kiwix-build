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
        return self.toolchains[0].builder

    @property
    def sdk_builder(self):
        return self.toolchains[1].builder

    def get_cross_config(self):
        install_path = self.ndk_builder.install_path
        return {
            'exec_wrapper_def': '',
            'install_path': install_path,
            'binaries': self.binaries(install_path),
            'root_path': pj(install_path, 'sysroot'),
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
        env['ANDROID_HOME'] = self.sdk_builder.install_path

AndroidPlatformInfo('android_arm', 'arm')
AndroidPlatformInfo('android_arm64', 'arm64')
AndroidPlatformInfo('android_mips', 'mips')
AndroidPlatformInfo('android_mips64', 'mips64')
AndroidPlatformInfo('android_x86', 'x86')
AndroidPlatformInfo('android_x86_64', 'x86_64')
