from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder
)

from kiwixbuild.utils import Remotefile, run_command


class Gumbo(Dependency):
    name = "gumbo"

    class Source(ReleaseDownload):
        archive = Remotefile('gumbo-0.10.1.tar.gz',
                             '28463053d44a5dfbc4b77bcf49c8cee119338ffa636cc17fc3378421d714efad',
                             'https://github.com/google/gumbo-parser/archive/v0.10.1.tar.gz')

        def _post_prepare_script(self, context):
            context.try_skip(self.extract_path)
            command = "./autogen.sh"
            run_command(command, self.extract_path, context)

    class Builder(MakeBuilder):
        @property
        def configure_env(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'iOS':
                return {
                    '_format_CFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['CFLAGS']}",
                    '_format_LDFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['LDFLAGS']}"
                }
            return {}
