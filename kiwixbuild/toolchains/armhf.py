import os
import subprocess

from .base_toolchain import Toolchain
from kiwixbuild.dependency_utils import GitClone
from kiwixbuild.utils import Remotefile, which
pj = os.path.join

class armhf_toolchain(Toolchain):
    name = 'armhf'
    arch_full = 'arm-linux-gnueabihf'

    class Source(GitClone):
        git_remote = "https://github.com/raspberrypi/tools"
        git_dir = "raspberrypi-tools"

    @property
    def root_path(self):
        return pj(self.source_path, 'arm-bcm2708', 'gcc-linaro-arm-linux-gnueabihf-raspbian-x64')

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
        return {k:pj(self.root_path, 'bin', v)
                for k,v in binaries}

    @property
    def exec_wrapper_def(self):
        try:
            which('qemu-arm')
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exec_wrapper = 'qemu-arm'"

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = " -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CFLAGS']
        env['CXXFLAGS'] = " -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CXXFLAGS']
        env['LIBS'] = " ".join(self.buildEnv.cross_config['extra_libs']) + " " +env['LIBS']
        env['QEMU_LD_PREFIX'] = pj(self.root_path, "arm-linux-gnueabihf", "libc")
        env['QEMU_SET_ENV'] = "LD_LIBRARY_PATH={}".format(
            ':'.join([
                pj(self.root_path, "arm-linux-gnueabihf", "lib"),
                pj(self.buildEnv.install_dir, 'lib'),
                pj(self.buildEnv.install_dir, self.buildEnv.libprefix)
        ]))

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']
