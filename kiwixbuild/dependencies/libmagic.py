import os

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
)

from kiwixbuild.utils import Remotefile, pj, Defaultdict, SkipCommand, run_command
from kiwixbuild._global import get_target_step

class LibMagic(Dependency):
    name = "libmagic"

    class Source(ReleaseDownload):
        name = "libmagic"
        source_dir = "libmagic"
        archive = Remotefile('file-5.33.tar.gz',
                             '1c52c8c3d271cd898d5511c36a68059cda94036111ab293f01f83c3525b737c6',
                             'https://fossies.org/linux/misc/file-5.33.tar.gz')

    class Builder(MakeBuilder):

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
            command = "make -j4 {make_target} {make_option}".format(
                make_target=self.make_target,
                make_option=self.make_option
            )
            libmagic_native_builder = get_target_step('libmagic', 'native_static')
            env = Defaultdict(str, os.environ)
            env['PATH'] = ':'.join([pj(libmagic_native_builder.build_path, 'src'), env['PATH']])
            run_command(command, self.build_path, context, buildEnv=self.buildEnv, env=env)
