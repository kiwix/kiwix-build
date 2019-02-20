import shutil

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand



class zlib(Dependency):
    name = 'zlib'

    class Source(ReleaseDownload):
        archive = Remotefile('zlib-1.2.8.tar.gz',
                             '36658cb768a54c1d4dec43c3116c27ed893e88b02ecfcb44f2166f9c0b7f2a0d')
        patches = ['zlib_std_libname.patch']

    class Builder(MakeBuilder):
        dynamic_configure_option = "--shared"
        static_configure_option = "--static"
        make_install_target = 'install'
        configure_option_template = "{dep_options} {static_option} --prefix {install_dir} --libdir {libdir}"

        def _pre_build_script(self, context):
            context.try_skip(self.build_path)
            shutil.copytree(self.source_path, self.build_path)


        def _configure(self, context):
            if self.buildEnv.platformInfo.build == 'win32':
                raise SkipCommand()
            return super()._configure(context)

        @property
        def make_option(self):
            if self.buildEnv.platformInfo.build == 'win32':
                return "--makefile win32/Makefile.gcc PREFIX={host}- SHARED_MODE={static} INCLUDE_PATH={include_path} LIBRARY_PATH={library_path} BINARY_PATH={binary_path}".format(
                    host='i686-w64-mingw32',
                    static="0" if self.buildEnv.platformInfo.static else "1",
                    include_path=pj(self.buildEnv.install_dir, 'include'),
                    library_path=pj(self.buildEnv.install_dir, self.buildEnv.libprefix),
                    binary_path=pj(self.buildEnv.install_dir, 'bin'),
                    )
            return ""
