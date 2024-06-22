from .base import Dependency, ReleaseDownload, NoopBuilder

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zim-testing-suite-0.6.0.tar.gz",
            "5aa91349a2791c862217b4d2ddd002f08589146ec047f10d5fa1f5fd85d0ea92",
            "https://github.com/openzim/zim-testing-suite/releases/download/0.6.0/zim-testing-suite-0.6.0.tar.gz",
        )

    Builder = NoopBuilder
