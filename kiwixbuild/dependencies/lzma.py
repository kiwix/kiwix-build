from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder)

from kiwixbuild.utils import Remotefile

class lzma(Dependency):
    name = 'lzma'

    class Source(ReleaseDownload):
        archive = Remotefile('xz-5.2.7.tar.gz',
                             '06327c2ddc81e126a6d9a78b0be5014b976a2c0832f492dcfc4755d7facf6d33',
                             'https://altushost-swe.dl.sourceforge.net/project/lzmautils/xz-5.2.7.tar.gz'
                            )

    class Builder(MakeBuilder):
        @property
        def configure_option(self):
            return ("--disable-xz "
                    "--disable-xzdec "
                    "--disable-lzmadec "
                    "--disable-lzmainfo "
                    "--disable-lzma-links "
                    "--disable-scripts "
                    "--disable-doc "
                    "--disable-symbol-versions ")
