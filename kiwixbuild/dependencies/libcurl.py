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
            "https://github.com/curl/curl/releases/download/curl-8_4_0/curl-8.4.0.tar.xz",
        )
        meson_archive = Remotefile(
            "curl_8.4.0-2_patch.zip",
            "bbb6ae75225c36ef9bb336cface729794c7c070c623a003fff40bd416042ff6e",
            "https://wrapdb.mesonbuild.com/v2/curl_8.4.0-2/get_patch",
        )
        archives = [src_archive, meson_archive]

    class Builder(MesonBuilder):
        dependencies = ["zlib"]

        @property
        def configure_options(self):
            yield from (
                f"-D{p}=disabled"
                for p in (
                    "ssh",
                    "ssl",
                    "rtmp",
                    "http2",
                    "idn",
                    "brotli",
                    "ftp",
                    "file",
                    "ldap",
                    "ldaps",
                    "rtsp",
                    "proxy",
                    "dict",
                    "telnet",
                    "tftp",
                    "pop3",
                    "imap",
                    "smb",
                    "smtp",
                    "mqtt",
                    "gopher",
                )
            )
