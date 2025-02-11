from .base import Dependency, ReleaseDownload, NoopBuilder

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zim-testing-suite-0.7.0.tar.gz",
            "b2da1d96973c9dfd8857f96850b40755a52813189ee961881bbddcd1e28aace4",
            "https://github.com/openzim/zim-testing-suite/releases/download/0.7.0/zim-testing-suite-0.7.0.tar.gz",
        )

    Builder = NoopBuilder
