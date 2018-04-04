import os

from .base_toolchain import Toolchain
from kiwixbuild.dependency_utils import ReleaseDownload, Builder
from kiwixbuild.utils import Remotefile, add_execution_right

pj = os.path.join

class android_ndk(Toolchain):
    name = 'android-ndk'
    version = 'r13b'
    gccver = '4.9.x'

    @property
    def api(self):
        return '21' if self.arch in ('arm64', 'mips64', 'x86_64') else '14'

    @property
    def platform(self):
        return 'android-'+self.api

    @property
    def arch(self):
        return self.buildEnv.platform_info.arch

    @property
    def arch_full(self):
        return self.buildEnv.platform_info.arch_full

    @property
    def toolchain(self):
        return self.arch_full+"-4.9"

    @property
    def root_path(self):
        return pj(self.builder.install_path, 'sysroot')

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
        return {k:pj(self.builder.install_path, 'bin', v)
                for k,v in binaries}

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    @property
    def full_name(self):
        return "{name}-{version}-{arch}-{api}".format(
            name = self.name,
            version = self.version,
            arch = self.arch,
            api = self.api)

    class Source(ReleaseDownload):
        archive = Remotefile('android-ndk-r13b-linux-x86_64.zip',
                             '3524d7f8fca6dc0d8e7073a7ab7f76888780a22841a6641927123146c3ffd29c',
                             'https://dl.google.com/android/repository/android-ndk-r13b-linux-x86_64.zip')

        @property
        def source_dir(self):
            return "{}-{}".format(
                self.target.name,
                self.target.version)


    class Builder(Builder):

        @property
        def install_path(self):
            return self.build_path

        def _build_platform(self, context):
            context.try_skip(self.build_path)
            script = pj(self.source_path, 'build/tools/make_standalone_toolchain.py')
            add_execution_right(script)
            command = '{script} --arch={arch} --api={api} --install-dir={install_dir} --force'
            command = command.format(
                script=script,
                arch=self.target.arch,
                api=self.target.api,
                install_dir=self.install_path
            )
            self.buildEnv.run_command(command, self.build_path, context)

        def _fix_permission_right(self, context):
            context.try_skip(self.build_path)
            bin_dirs = [pj(self.install_path, 'bin'),
                        pj(self.install_path, self.target.arch_full, 'bin'),
                        pj(self.install_path, 'libexec', 'gcc', self.target.arch_full, self.target.gccver)
                       ]
            for root, dirs, files in os.walk(self.install_path):
                if not root in bin_dirs:
                    continue

                for file_ in files:
                    file_path = pj(root, file_)
                    if os.path.islink(file_path):
                        continue
                    add_execution_right(file_path)

        def build(self):
            self.command('build_platform', self._build_platform)
            self.command('fix_permission_right', self._fix_permission_right)

    def get_bin_dir(self):
        return [pj(self.builder.install_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(self.root_path) + env['CFLAGS']
        env['CXXFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(self.root_path) + env['CXXFLAGS']
        env['LDFLAGS'] = '--sysroot={} '.format(self.root_path) + env['LDFLAGS']
        #env['CFLAGS'] = ' -fPIC -D_FILE_OFFSET_BITS=64 -O3 '+env['CFLAGS']
        #env['CXXFLAGS'] = (' -D__OPTIMIZE__ -fno-strict-aliasing '
        #                   ' -DU_HAVE_NL_LANGINFO_CODESET=0 '
        #                   '-DU_STATIC_IMPLEMENTATION -O3 '
        #                   '-DU_HAVE_STD_STRING -DU_TIMEZONE=0 ')+env['CXXFLAGS']
        env['NDK_DEBUG'] = '0'

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']

