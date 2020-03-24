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
        archive = Remotefile('xapian-core-1.4.14.tar.xz',
                             '975a7ac018c9d34a15cc94a3ecc883204403469f748907e5c4c64d0aec2e4949')
        patches = [
            'xapian_sys_types.patch',
            'xapian_fix_include_errno.patch',
            'xapian_remote.patch'
        ]

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-chert --disable-backend-remote --disable-backend-inmemory --disable-documentation"
        configure_env = {'_format_LDFLAGS': "{env.LDFLAGS} -L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS': "{env.CXXFLAGS} -O3 -I{buildEnv.install_dir}/include"}


        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            deps = ['zlib', 'lzma']
            if (platformInfo.build == 'win32'
             or neutralEnv('distname') == 'Darwin'):
                return deps
            return deps + ['uuid']
