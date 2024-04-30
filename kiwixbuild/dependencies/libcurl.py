from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
)

from kiwixbuild.utils import Remotefile


class LibCurl(Dependency):
    name = "libcurl"

    class Source(ReleaseDownload):
        name = "libcurl"
        archive = Remotefile(
            "curl-7.67.0.tar.xz",
            "f5d2e7320379338c3952dcc7566a140abb49edb575f9f99272455785c40e536c",
            "https://curl.haxx.se/download/curl-7.67.0.tar.xz",
        )

    class Builder(MakeBuilder):
        dependencies = ["zlib"]
        configure_options = [
            *[
                f"--without-{p}"
                for p in (
                    "libssh2",
                    "ssl",
                    "libmetalink",
                    "librtmp",
                    "nghttp2",
                    "libidn2",
                    "brotli",
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
                    "manual",
                )
            ],
        ]
