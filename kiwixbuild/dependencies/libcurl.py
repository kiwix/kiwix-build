import os

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
)

from kiwixbuild.utils import Remotefile, pj, Defaultdict, SkipCommand, run_command
from kiwixbuild._global import get_target_step

class LibCurl(Dependency):
    name = "libcurl"

    class Source(ReleaseDownload):
        name = "libcurl"
        archive = Remotefile('curl-7.61.0.tar.xz',
                             'ef6e55192d04713673b4409ccbcb4cb6cd723137d6e10ca45b0c593a454e1720',
                             'https://curl.haxx.se/download/curl-7.61.0.tar.xz')

    class Builder(MakeBuilder):
        dependencies = ['zlib']
        _configure_option = " ".join(
            ["--without-{}".format(p)
                for p in ('libssh2', 'ssl', 'libmetalink', 'librtmp')] +
            ["--disable-{}".format(p)
                for p in ('ftp', 'file', 'ldap', 'ldaps', 'rtsp', 'dict',
                          'telnet', 'tftp', 'pop3', 'imap', 'smb', 'smtp',
                          'gopher', 'manual')])

        @property
        def configure_option(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'iOS':
                return self._configure_option + " --disable-unix-sockets"
            return self._configure_option

        @property
        def configure_env(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'iOS':
                return {
                    '_format_CFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['CFLAGS']}",
                    '_format_LDFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['LDFLAGS']}"
                }
            return {}
