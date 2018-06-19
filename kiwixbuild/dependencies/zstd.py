from .base import (
    Dependency,
    ReleaseDownload,
    MesonBuilder)

from kiwixbuild.utils import Remotefile



class zstd(Dependency):
    name = 'zstd'

    class Source(ReleaseDownload):
        archive = Remotefile('zstd-1.5.2.tar.gz',
                             'f7de13462f7a82c29ab865820149e778cbfe01087b3a55b5332707abf9db4a6e',
                             'https://github.com/facebook/zstd/archive/refs/tags/v1.5.2.tar.gz')

    class Builder(MesonBuilder):
        subsource_dir = 'build/meson'
        build_type = 'release'
        strip_options = []
        configure_options = ['-Dbin_programs=false', '-Dbin_contrib=false']
