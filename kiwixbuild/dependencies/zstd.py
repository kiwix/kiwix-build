from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile



class zstd(Dependency):
    name = 'zstd'

    class Source(ReleaseDownload):
        archive = Remotefile('zstd-1.4.4.tar.gz',
                             '59ef70ebb757ffe74a7b3fe9c305e2ba3350021a918d168a046c6300aeea9315',
                             'https://github.com/facebook/zstd/releases/download/v1.4.4/zstd-1.4.4.tar.gz')
        patches = ['zstd_meson.patch']

    class Builder(MesonBuilder):
        subsource_dir = 'build/meson'
        build_type = 'release'
        strip_option = ''
        configure_option = '-Dbin_programs=false -Dbin_contrib=false'
