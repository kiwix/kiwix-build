from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class MicroHttpd(Dependency):
    name = "libmicrohttpd"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.63.tar.gz',
                             '37c36f1be177f0e37ef181a645cd3baac1000bd322a01c2eff70f3cc8c91749c',
                             'https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.63.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl --disable-doc --disable-examples"
