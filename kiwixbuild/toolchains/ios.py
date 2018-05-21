from .base_toolchain import Toolchain

from kiwixbuild.utils import pj, xrun_find

class iOS_sdk(Toolchain):
    @property
    def root_path(self):
        return self.buildEnv.platform_info.root_path

    @property
    def binaries(self):
        return {
            'CC': xrun_find('clang'),
            'CXX': xrun_find('clang++'),
            'AR': '/usr/bin/ar',
            'STRIP': '/usr/bin/strip',
            'RANLIB': '/usr/bin/ranlib',
            'LD': '/usr/bin/ld',
        }

    @property
    def configure_option(self):
        return '--host=arm-apple-darwin'

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        arch = self.buildEnv.platform_info.arch
        env['CFLAGS'] = " -fembed-bitcode -isysroot {SDKROOT} -arch {arch} -miphoneos-version-min=9.0 ".format(SDKROOT=self.root_path, arch=arch) + env['CFLAGS']
        env['CXXFLAGS'] = env['CFLAGS'] + " -stdlib=libc++ -std=c++11 "+env['CXXFLAGS']
        env['LDFLAGS'] = " -arch {arch} -isysroot {SDKROOT} ".format(SDKROOT=self.root_path, arch=arch)
        env['MACOSX_DEPLOYMENT_TARGET'] = "10.7"

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']
