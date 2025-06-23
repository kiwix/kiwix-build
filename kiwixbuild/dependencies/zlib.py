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
        src_archive = Remotefile(
            "zlib-1.3.1.tar.gz", # https://zlib.net/zlib-1.3.1.tar.gz
            "9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23"
        )
        meson_patch = Remotefile(
            "zlib_1.3.1-1_patch.zip", # https://wrapdb.mesonbuild.com/v2/zlib_1.3.1-1/get_patch
            "e79b98eb24a75392009cec6f99ca5cdca9881ff20bfa174e8b8926d5c7a47095"
        )
        archives = [src_archive, meson_patch]
        #patches = ['zlib_std_libname.patch']

    Builder = MesonBuilder
