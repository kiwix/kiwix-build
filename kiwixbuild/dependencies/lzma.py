from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class lzma(Dependency):
    name = 'lzma'

    class Source(ReleaseDownload):
        archive = Remotefile('xz-5.2.4.tar.gz',
                             'b512f3b726d3b37b6dc4c8570e137b9311e7552e8ccbab4d39d47ce5f4177145'
                            )

    class Builder(MakeBuilder):
        @property
        def configure_option(self):
            return "--disable-xz --disable-xzdec"

        @property
        def configure_env(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'iOS':
                return {
                    '_format_CFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['CFLAGS']}",
                    '_format_LDFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['LDFLAGS']}"
                }
            return {}
