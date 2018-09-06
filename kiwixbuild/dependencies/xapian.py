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
        archive = Remotefile('xapian-core-1.4.5.tar.xz',
                             '85b5f952de9df925fd13e00f6e82484162fd506d38745613a50b0a2064c6b02b')
        patches = ['xapian_sys_types.patch']

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-chert --disable-backend-inmemory --disable-documentation"
        configure_env = {'_format_LDFLAGS': "-L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS': "-I{buildEnv.install_dir}/include"}

        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            if (platformInfo.build == 'flatpak'):
                return []
            deps = ['zlib', 'lzma']
            if (platformInfo.build == 'win32'
             or neutralEnv('distname') == 'Darwin'):
                return deps
            return deps + ['uuid']
