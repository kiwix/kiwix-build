import os
import subprocess

from .base_toolchain import Toolchain
from kiwixbuild.utils import which

pj = os.path.join

class mingw32_toolchain(Toolchain):
    name = 'mingw32'
    arch_full = 'i686-w64-mingw32'
    extra_libs = ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4', '-lmsvcr90', '-liphlpapi']

    @property
    def root_path(self):
        root_paths = {
            'fedora': '/usr/i686-w64-mingw32/sys-root/mingw',
            'debian': '/usr/i686-w64-mingw32'
        }
        return root_paths[self.neutralEnv.distname]

    @property
    def binaries(self):
        return {k:which('{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'))
               }

    @property
    def exec_wrapper_def(self):
        try:
            which('wine')
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exec_wrapper = 'wine'"

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['LIBS'] = " ".join(self.extra_libs) + " " +env['LIBS']
