from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class MicroHttpd(Dependency):
    name = "libmicrohttpd"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.69.tar.gz',
                             'fb9b6b148b787493e637d3083588711e65cbcb726fa02cee2cd543c5de27e37e',
                             'https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.69.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl --disable-doc --disable-examples"
