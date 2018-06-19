import shutil

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand



class zlib(Dependency):
    name = 'zlib'

    class Source(ReleaseDownload):
        archive = Remotefile('zlib-1.2.12.tar.gz',
                             '91844808532e5ce316b3c010929493c0244f3d37593afd6de04f71821d5136d9')
        patches = ['zlib_std_libname.patch']

    class Builder(MakeBuilder):
        dynamic_configure_options = ["--shared"]
        static_configure_options = ["--static"]
        make_install_targets = ['install']

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
            if self.buildEnv.platformInfo.build != 'win32':
                return
            yield "--makefile"
            yield "win32/Makefile.gcc"
            yield "PREFIX=i686-w64-mingw32-",
            yield "SHARED_MODE={}".format("0" if self.buildEnv.platformInfo.static else "1"),
            yield "INCLUDE_PATH={}".format(pj(self.buildEnv.install_dir, 'include')),
            yield "LIBRARY_PATH={}".format(pj(self.buildEnv.install_dir, self.buildEnv.libprefix)),
            yield "BINARY_PATH={}".format(pj(self.buildEnv.install_dir, 'bin'))

        @property
        def make_targets(self):
            if self.buildEnv.platformInfo.static:
                return ["static"]
            else:
                return ["shared"]
