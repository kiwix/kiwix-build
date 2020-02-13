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
        archive = Remotefile('curl-7.67.0.tar.xz',
                             'f5d2e7320379338c3952dcc7566a140abb49edb575f9f99272455785c40e536c',
                             'https://curl.haxx.se/download/curl-7.67.0.tar.xz')

    class Builder(MakeBuilder):
        dependencies = ['zlib']
        configure_option = " ".join(
            ["--without-{}".format(p)
                for p in ('libssh2', 'ssl', 'libmetalink', 'librtmp')] +
            ["--disable-{}".format(p)
                for p in ('ftp', 'file', 'ldap', 'ldaps', 'rtsp', 'dict',
                          'telnet', 'tftp', 'pop3', 'imap', 'smb', 'smtp',
                          'gopher', 'manual')])

        @property
        def configure_env(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'iOS':
                return {
                    '_format_CFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['CFLAGS']}",
                    '_format_LDFLAGS' : "-arch {buildEnv.platformInfo.arch} {env['LDFLAGS']}"
                }
            return {}
