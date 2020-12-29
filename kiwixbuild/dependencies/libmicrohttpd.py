from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class MicroHttpd(Dependency):
    name = "libmicrohttpd"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.72.tar.gz',
                             '0ae825f8e0d7f41201fd44a0df1cf454c1cb0bc50fe9d59c26552260264c2ff8',
                             'https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.72.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl --disable-doc --disable-examples"
