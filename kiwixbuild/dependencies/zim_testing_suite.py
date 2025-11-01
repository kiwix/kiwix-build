from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile


class ZimTestingSuite(Dependency):
    name = "zim-testing-suite"
    version = "0.8.0"  
    dont_skip = True

    class Source(ReleaseDownload):
        archive = Remotefile(
            f"zim-testing-suite-{ZimTestingSuite.version}.tar.gz",  
            "28f51449a3f9aea02652ca21f32c5598fd610d6cec3810fa552bd0c0f7a2d5fc",
            f"https://github.com/openzim/zim-testing-suite/releases/download/{ZimTestingSuite.version}/zim-testing-suite-{ZimTestingSuite.version}.tar.gz",  # ✅ Dynamic URL
        )

    Builder = NoopBuilder
