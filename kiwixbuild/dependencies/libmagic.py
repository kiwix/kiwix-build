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
        archive_top_dir = 'file-5.35'
        archive = Remotefile('file-5.35.tar.gz',
                             '30c45e817440779be7aac523a905b123cba2a6ed0bf4f5439e1e99ba940b5546')

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

        @property
        def configure_env(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'iOS':
                return {
                    '_format_CFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['CFLAGS']}",
                    '_format_LDFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['LDFLAGS']}"
                }
            return {}
