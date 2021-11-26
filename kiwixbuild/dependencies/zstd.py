from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile



class zstd(Dependency):
    name = 'zstd'

    class Source(ReleaseDownload):
        archive = Remotefile('zstd-1.5.0.tar.gz',
                             '5194fbfa781fcf45b98c5e849651aa7b3b0a008c6b72d4a0db760f3002291e94',
                             'https://github.com/facebook/zstd/releases/download/v1.5.0/zstd-1.5.0.tar.gz')
        patches = ['zstd_meson.patch']

    class Builder(MesonBuilder):
        subsource_dir = 'build/meson'
        build_type = 'release'
        strip_option = ''
        configure_option = '-Dbin_programs=false -Dbin_contrib=false'
