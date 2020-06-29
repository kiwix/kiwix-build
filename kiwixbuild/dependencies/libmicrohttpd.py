from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class MicroHttpd(Dependency):
    name = "libmicrohttpd"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.71.tar.gz',
                             'e8f445e85faf727b89e9f9590daea4473ae00ead38b237cf1eda55172b89b182',
                             'https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.71.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl --disable-doc --disable-examples"
