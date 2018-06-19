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
        dynamic_configure_options = ["--shared"]
        static_configure_options = ["--static"]

        def _pre_build_script(self, context):
            context.try_skip(self.build_path)
            shutil.copytree(self.source_path, self.build_path)


        def _configure(self, context):
            if self.buildEnv.platformInfo.build == 'win32':
                raise SkipCommand()
            return super()._configure(context)

        @property
        def all_configure_options(self):
            yield from self.configure_options
            yield from self.static_configure_options if self.buildEnv.platformInfo.static else self.dynamic_configure_options
            yield from ('--prefix', self.buildEnv.install_dir)
            yield from ('--libdir', pj(self.buildEnv.install_dir, self.buildEnv.libprefix))

        @property
        def make_options(self):
            if self.buildEnv.platformInfo.build == 'win32':
                return
            yield "--makefile"
            yield "{}/Makefile.gcc".format(self.buildEnv.platformInfo.build)
            yield "PREFIX={}-".format(self.buildEnv.platformInfo.arch_full)
            yield "SHARED_MODE={}".format("0" if self.buildEnv.platformInfo.static else "1")
            yield "INCLUDE_PATH={}".format(pj(self.buildEnv.install_dir, 'include'))
            yield "LIBRARY_PATH={}".format(pj(self.buildEnv.install_dir, self.buildEnv.libprefix))
            yield "BINARY_PATH={}".format(pj(self.buildEnv.install_dir, 'bin'))
