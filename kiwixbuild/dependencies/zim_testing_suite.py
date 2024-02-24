from .base import Dependency, ReleaseDownload, NoopBuilder

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zim-testing-suite-0.5.tar.gz",
            "3ffd7e0adf46e9a44cad463f4220d2406a700e95deeff936463be818acf47256",
            "https://github.com/openzim/zim-testing-suite/releases/download/v0.5/zim-testing-suite-0.5.tar.gz",
        )

    Builder = NoopBuilder
