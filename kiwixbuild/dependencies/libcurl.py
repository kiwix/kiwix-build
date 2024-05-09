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
        archive = Remotefile(
            "curl-8.7.1.tar.xz",
            "6fea2aac6a4610fbd0400afb0bcddbe7258a64c63f1f68e5855ebc0c659710cd",
            "https://curl.se/download/curl-8.7.1.tar.xz",
        )

    class Builder(MakeBuilder):
        dependencies = ["zlib"]
        configure_options = [
            *[
                f"--without-{p}"
                for p in (
                    "libssh2",
                    "ssl",
                    "librtmp",
                    "nghttp2",
                    "nghttp3",
                    "libidn2",
                    "brotli",
                    "hyper",
                )
            ],
            *[
                f"--disable-{p}"
                for p in (
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
                    "mqtt",
                    "docs",
                    "manual",
                )
            ],
        ]
