from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile

class aarch64_musl_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "aarch64_musl"

    class Source(ReleaseDownload):
        archive = Remotefile('aarch64-linux-musl-cross.tgz',
                             'c909817856d6ceda86aa510894fa3527eac7989f0ef6e87b5721c58737a06c38',
                             'https://musl.cc/aarch64-linux-musl-cross.tgz')

    Builder = NoopBuilder


class x86_64_musl_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "x86-64_musl"

    class Source(ReleaseDownload):
        archive = Remotefile('x86_64-linux-musl-cross.tgz',
                             '',
                             'https://musl.cc/x86_64-linux-musl-cross.tgz')

    Builder = NoopBuilder
