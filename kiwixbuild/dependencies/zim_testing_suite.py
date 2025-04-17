from .base import Dependency, ReleaseDownload, NoopBuilder

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zim-testing-suite-0.8.0.tar.gz",
            "28f51449a3f9aea02652ca21f32c5598fd610d6cec3810fa552bd0c0f7a2d5fc",
            "https://github.com/openzim/zim-testing-suite/releases/download/0.8.0/zim-testing-suite-0.8.0.tar.gz",
        )

    Builder = NoopBuilder
