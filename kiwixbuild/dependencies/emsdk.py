import os

from .base import Dependency, ReleaseDownload, Builder
from kiwixbuild.utils import Remotefile, run_command, copy_tree

pj = os.path.join

class emsdk(Dependency):
    dont_skip = True
    neutral = False
    name = 'emsdk'

    class Source(ReleaseDownload):
        archive = Remotefile('emsdk-3.1.24.tar.gz',
                             '1aa5365ccb2147701cc9d1e59a5a49577c1d6aea55da7c450df2d5ffa48b8a58',
                             'https://codeload.github.com/emscripten-core/emsdk/tar.gz/refs/tags/3.1.24')

        @property
        def source_dir(self):
            return self.target.full_name()


    class Builder(Builder):
        @property
        def install_path(self):
            return self.build_path

        def _copy_source(self, context):
            context.try_skip(self.build_path)
            copy_tree(self.source_path, self.build_path)

        def _install(self, context):
            context.try_skip(self.build_path)
            command = "./emsdk install 3.1.24"
            run_command(command, self.build_path, context)

        def _activate(self, context):
            context.try_skip(self.build_path)
            command = "./emsdk activate 3.1.24"
            run_command(command, self.build_path, context)


        def build(self):
            self.command('copy_source', self._copy_source)
            self.command('install', self._install)
            self.command('activate', self._activate)

