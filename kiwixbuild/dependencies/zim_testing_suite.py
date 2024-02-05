from .base import Dependency, ReleaseDownload, NoopBuilder

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zim-testing-suite-0.3.tar.gz",
            "cd7d1ccc48af3783af9156cb6bf3c18d9a3319a73fdeefe65f0b4cae402d3d66",
            "https://github.com/openzim/zim-testing-suite/releases/download/v0.3/zim-testing-suite-0.3.tar.gz",
        )

    Builder = NoopBuilder
