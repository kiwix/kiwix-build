from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile


class lzma(Dependency):
    name = 'lzma'
    version = '5.2.6'

    class Source(ReleaseDownload):
        src_archive = Remotefile(
            f"xz-{lzma.version}.tar.gz",
            "a2105abee17bcd2ebd15ced31b4f5eda6e17efd6b10f921a01cda4a44c91b3a0",
           url= "https://altushost-swe.dl.sourceforge.net/project/lzmautils/xz-5.2.6.tar.gz",
        )
        meson_patch = Remotefile(
            f"liblzma_{lzma.version}_patch.zip",
            "1c71536d364e1a3ce6bea61266576f89cc5cce4d3b9e11f3494417dafa29780b",
            url="https://wrapdb.mesonbuild.com/v2/liblzma_5.2.6-3/get_patch",
        )
        archives = [src_archive, meson_patch]
        patches = ['lzma_meson_install.patch']

    Builder = MesonBuilder
