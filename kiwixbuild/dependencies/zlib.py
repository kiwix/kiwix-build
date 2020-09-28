import shutil

from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand
from kiwixbuild._global import neutralEnv


class zlib(Dependency):
    name = "zlib"

    class Source(ReleaseDownload):
        src_archive = Remotefile("zlib-1.2.12.tar.gz",
                                 "91844808532e5ce316b3c010929493c0244f3d37593afd6de04f71821d5136d9")
        meson_patch = Remotefile("zlib_1.2.12-1_patch.zip",
                                 "8ec8344f3fe7b06ad4be768fd416694bc56cb4545ce78b0f1c18b3e72b3ec936",
                                 "https://wrapdb.mesonbuild.com/v2/zlib_1.2.12-1/get_patch")
        archives = [src_archive, meson_patch]
        #patches = ['zlib_std_libname.patch']

    Builder = MesonBuilder
