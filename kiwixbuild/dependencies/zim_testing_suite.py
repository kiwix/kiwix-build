from .base import Dependency, ReleaseDownload, NoopBuilder

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zim-testing-suite-0.9.0.tar.gz",
            "1192a4552c5a455c5219a732657d3dbfb5fd6f5ddab206f9cbb913b1ba09a99c",
            "https://github.com/openzim/zim-testing-suite/releases/download/0.9.0/zim-testing-suite-0.9.0.tar.gz",
        )

    Builder = NoopBuilder
