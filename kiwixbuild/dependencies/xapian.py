from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder
)

from kiwixbuild.utils import Remotefile
from kiwixbuild._global import neutralEnv


class Xapian(Dependency):
    name = "xapian-core"

    class Source(ReleaseDownload):
        archive = Remotefile('xapian-core-1.4.22.tar.xz',
                             '05884af00b06702ce486057d62a3bfbe6606cf965ada0f5ea570b328a2fa1ea8')
        patches = ['xapian_win32.patch']

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-chert --disable-backend-remote --disable-documentation"
        configure_env = {'_format_LDFLAGS': "{env.LDFLAGS} -L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS': "{env.CXXFLAGS} -O3 -I{buildEnv.install_dir}/include"}


        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            deps = ['zlib', 'lzma']
            if (platformInfo.build in ('win32', 'wasm')
             or neutralEnv('distname') == 'Darwin'):
                return deps
            return deps + ['uuid']
