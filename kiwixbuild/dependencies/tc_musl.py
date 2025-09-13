from .base import Dependency, ReleaseDownload, TcCopyBuilder
from kiwixbuild.utils import Remotefile


class aarch64_musl_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "aarch64_musl"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "aarch64-linux-musl-cross.tgz",
            "0f18a885b161815520bbb5757a4b4ab40d0898c29bebee58d0cddd6112e59cc6",
#            "https://more.musl.cc/10/x86_64-linux-musl/aarch64-linux-musl-cross.tgz",
             "https://dev.kiwix.org/kiwix-build/aarch64-linux-musl-cross.tgz"
        )

    Builder = TcCopyBuilder


class x86_64_musl_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "x86-64_musl"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "x86_64-linux-musl-cross.11.tgz",
            "c6226824d6b7214ce974344b186179c9fa89be3c33dd7431c4b6585649ce840b",
            "https://more.musl.cc/11/x86_64-linux-musl/x86_64-linux-musl-cross.tgz",
#            "https://dev.kiwix.org/kiwix-build/x86_64-linux-musl-cross.tgz"
        )

    Builder = TcCopyBuilder
