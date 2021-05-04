from .base import (
    Dependency,
    ReleaseDownload,
    NoopBuilder
)

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile('zim-testing-suite-0.2.tar.gz',
                             '04a6db258a48a09ebf25fdf5856029f11269190467b46d54e02c26f2236e2b32',
                             'https://github.com/openzim/zim-testing-suite/releases/download/v0.2/zim-testing-suite-0.2.tar.gz')

    Builder = NoopBuilder
