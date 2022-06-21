import shutil

from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand
from kiwixbuild._global import neutralEnv


class zlib(Dependency):
    name = 'zlib'

    class Source(ReleaseDownload):
        archive = Remotefile('zlib-1.2.12.tar.gz',
                             '91844808532e5ce316b3c010929493c0244f3d37593afd6de04f71821d5136d9')
        patches = ['zlib_meson.patch']

    class Builder(MesonBuilder):
        pass
