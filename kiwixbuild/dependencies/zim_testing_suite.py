from .base import Dependency, ReleaseDownload, NoopBuilder

from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zim-testing-suite-0.10.0.tar.gz",
            "348821681a8f10eac8b7ca01dd48645d5b9a9c7d5b723edb0503d7d7f1042a96",
            "https://github.com/openzim/zim-testing-suite/releases/download/0.10.0/zim-testing-suite-0.10.0.tar.gz",
        )

    Builder = NoopBuilder
