from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class lzma(Dependency):
    name = 'lzma'

    class Source(ReleaseDownload):
        archive = Remotefile('xz-5.2.3.tar.bz2',
                             'fd9ca16de1052aac899ad3495ad20dfa906c27b4a5070102a2ec35ca3a4740c1',
                             'https://tukaani.org/xz/xz-5.2.3.tar.bz2')

    class Builder(MakeBuilder):
        @property
        def configure_option(self):
            return "--disable-assembler --disable-xz --disable-xzdec"
