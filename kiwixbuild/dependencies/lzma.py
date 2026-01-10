from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile


class lzma(Dependency):
    name = 'lzma'

    class Source(ReleaseDownload):
        src_archive = Remotefile(
            "xz-5.2.6.tar.gz",
            "a2105abee17bcd2ebd15ced31b4f5eda6e17efd6b10f921a01cda4a44c91b3a0",
            "https://dev.kiwix.org/kiwix-build/xz-5.2.6.tar.gz",
        )
        meson_patch = Remotefile(
            "liblzma_5.2.6-3_patch.zip",
            "1c71536d364e1a3ce6bea61266576f89cc5cce4d3b9e11f3494417dafa29780b",
            "https://dev.kiwix.org/kiwix-build/liblzma_5.2.6-3_patch.zip",
        )
        archives = [src_archive, meson_patch]
        patches = ['lzma_meson_install.patch']

    Builder = MesonBuilder
