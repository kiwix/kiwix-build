import shutil

from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand



class zlib(Dependency):
    name = 'zlib'

    class Source(ReleaseDownload):
        archive = Remotefile('zlib-1.2.11.tar.gz',
                             'c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1',
                             'http://zlib.net/fossils/zlib-1.2.11.tar.gz')
        patches = ['zlib_meson.patch']

    class Builder(MesonBuilder):
        pass
