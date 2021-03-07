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
        archive = Remotefile('xapian-core-1.4.18.tar.xz',
                             '196ddbb4ad10450100f0991a599e4ed944cbad92e4a6fe813be6dce160244b77')
        patches = [
            'xapian_sys_types.patch',
            'xapian_fix_include_errno.patch',
            'xapian_remote.patch'
        ]

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-chert --disable-backend-remote --disable-documentation"
        configure_env = {'_format_LDFLAGS': "{env.LDFLAGS} -L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS': "{env.CXXFLAGS} -O3 -I{buildEnv.install_dir}/include"}


        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            deps = ['zlib', 'lzma']
            if (platformInfo.build == 'win32'
             or neutralEnv('distname') == 'Darwin'):
                return deps
            return deps + ['uuid']
