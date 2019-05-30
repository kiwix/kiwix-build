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
        archive = Remotefile('xapian-core-1.4.10.tar.xz',
                             '68669327e08544ac88fe3473745dbcae4e8e98d5060b436c4d566f1f78709bb8')
        patches = [
            'xapian_sys_types.patch',
            'xapian_fix_include_errno.patch',
            'xapian_configure.patch'
        ]

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-chert --disable-backend-inmemory --disable-documentation"
        configure_env = {'_format_LDFLAGS': "{env.LDFLAGS} -L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS': "{env.CXXFLAGS} -I{buildEnv.install_dir}/include"}


        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            deps = ['zlib', 'lzma']
            if (platformInfo.build == 'win32'
             or neutralEnv('distname') == 'Darwin'):
                return deps
            return deps + ['uuid']
