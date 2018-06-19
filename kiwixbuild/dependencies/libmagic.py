import os

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
)

from kiwixbuild.utils import Remotefile, pj, SkipCommand, run_command
from kiwixbuild._global import get_target_step

class LibMagic(Dependency):
    name = "libmagic"

    class Source(ReleaseDownload):
        name = "libmagic"
        source_dir = "libmagic"
        archive_top_dir = 'file-5.44'
        archive = Remotefile('file-5.44.tar.gz',
                             '3751c7fba8dbc831cb8d7cc8aff21035459b8ce5155ef8b0880a27d028475f3b')

    class Builder(MakeBuilder):
        @property
        def configure_options(self):
            yield "--disable-bzlib"
            yield "--disable-xzlib"
            yield "--disable-zstdlib"
            yield "--disable-lzlib"

        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            if platformInfo.build != 'native':
                return [('native_static', 'libmagic')]
            return []

        def _compile(self, context):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'native':
                return super()._compile(context)
            context.try_skip(self.build_path)
            command = [
                "make",
                "-j4",
                *self.make_targets,
                *self.make_options
            ]
            env = self.buildEnv.get_env(cross_comp_flags=True, cross_compilers=True, cross_path=True)
            libmagic_native_builder = get_target_step('libmagic', 'native_static')
            env['PATH'] = ':'.join([pj(libmagic_native_builder.build_path, 'src'), env['PATH']])
            run_command(command, self.build_path, context, env=env)
