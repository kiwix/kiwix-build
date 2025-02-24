import os

from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder,
)

from kiwixbuild.utils import Remotefile, pj, Defaultdict, SkipCommand, run_command
from kiwixbuild._global import get_target_step


class LibCurl(Dependency):
    name = "libcurl"

    class Source(ReleaseDownload):
        name = "libcurl"
        src_archive = Remotefile(
            "curl-8.4.0.tar.xz",
            "16c62a9c4af0f703d28bda6d7bbf37ba47055ad3414d70dec63e2e6336f2a82d",
            "https://curl.se/download/curl-8.4.0.tar.xz",
        )
        meson_archive = Remotefile(
            "curl_8.4.0-2_patch.zip",
            "bbb6ae75225c36ef9bb336cface729794c7c070c623a003fff40bd416042ff6e",
            "https://dev.kiwix.org/libkiwix/curl_8.4.0-2_patch.zip",
        )
        archives = [src_archive, meson_archive]

    class Builder(MesonBuilder):
        dependencies = ["zlib"]
        configure_options = [
            f"-D{p}=disabled"
            for p in (
                "psl",
                "kerberos-auth",
                "gss-api",
                "ssh",
                "rtmp",
                "http2",
                "idn",
                "brotli",
                "ftp",
                "file",
                "ldap",
                "ldaps",
                "rtsp",
                "dict",
                "telnet",
                "tftp",
                "pop3",
                "imap",
                "smb",
                "smtp",
                "gopher",
                "tool",
            )
        ]

        def _test(self, context):
            context.skip("No Test")
