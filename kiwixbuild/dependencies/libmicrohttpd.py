from .base import Dependency, ReleaseDownload, MesonBuilder

from kiwixbuild.utils import Remotefile


class MicroHttpd(Dependency):
    name = "libmicrohttpd"

    class Source(ReleaseDownload):
        src_archive = Remotefile(
            "libmicrohttpd-0.9.76.tar.gz",
            "f0b1547b5a42a6c0f724e8e1c1cb5ce9c4c35fb495e7d780b9930d35011ceb4c",
            "https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.76.tar.gz",
        )
        meson_archive = Remotefile(
            "libmicrohttpd_0.9.16-3_patch.zip",
            "0954c094a0d4cfe0dd799d8df8a04face6669f7b4d51a7386a9c3e2d37b9c3b3",
            "https://wrapdb.mesonbuild.com/v2/libmicrohttpd_0.9.76-3/get_patch",
        )
        archives = [src_archive, meson_archive]
        patches = [
            "libmicrohttpd_meson_pkgconfig.patch",
            "libmicrohttpd_meson_timeval_tvsec_size.patch",
        ]

    class Builder(MesonBuilder):
        configure_options = [
            "-Dgnutls=disabled",
            "-Dgcrypt=disabled",
            "-Dcurl=disabled",
            "-Dexpat=disabled",
        ]
