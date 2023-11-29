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
            "",
            "https://github.com/curl/curl/releases/curl-8_4_0/curl-8.4.0.tar.xz",
        )
        meson_archive = Remotefile(
            "curl_8.4.0-2_patch.zip",
            "",
            "https://wrapdb.mesonbuild.com/v2/curl_8.4.0-2/get_path",
        )
        archive = [src_archive, meson_archive]

    class Builder(MesonBuilder):
        dependencies = ["zlib"]
        configure_options = [
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
                "dict",
                "telnet",
                "tftp",
                "pop3",
                "imap",
                "smb",
                "smtp",
                "gopher",
                "manual",
            )
        ]
