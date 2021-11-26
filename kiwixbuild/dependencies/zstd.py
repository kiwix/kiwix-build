from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile



class zstd(Dependency):
    name = 'zstd'

    class Source(ReleaseDownload):
        archive = Remotefile('zstd-1.5.1.tar.gz',
                             'e28b2f2ed5710ea0d3a1ecac3f6a947a016b972b9dd30242369010e5f53d7002',
                             'https://github.com/facebook/zstd/releases/download/v1.5.1/zstd-1.5.1.tar.gz')
        patches = ['zstd_meson.patch']

    class Builder(MesonBuilder):
        subsource_dir = 'build/meson'
        build_type = 'release'
        strip_option = ''
        configure_option = '-Dbin_programs=false -Dbin_contrib=false'
