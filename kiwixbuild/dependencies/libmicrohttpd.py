from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class MicroHttpd(Dependency):
    name = "libmicrohttpd"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.65.tar.gz',
                             'f2467959c5dd5f7fdf8da8d260286e7be914d18c99b898e22a70dafd2237b3c9',
                             'http://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.65.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl --disable-doc --disable-examples"
