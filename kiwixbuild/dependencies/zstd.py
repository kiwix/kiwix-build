from typing import ClassVar

from kiwixbuild.utils import Remotefile

from .base import Dependency, MesonBuilder, ReleaseDownload


class Zstd(Dependency):
    name = "zstd"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zstd-1.5.7.tar.gz",
            "eb33e51f49a15e023950cd7825ca74a4a2b43db8354825ac24fc1b7ee09e6fa3",
            "https://dev.kiwix.org/kiwix-build/zstd-1.5.7.tar.gz",
        )

        patches: ClassVar[list[str]] = [
            "zstd_qsort.patch",
        ]

    class Builder(MesonBuilder):
        subsource_dir = "build/meson"
        build_type = "release"
        strip_options: ClassVar[list] = []
        configure_options: ClassVar[list[str]] = [
            "-Dbin_programs=false",
            "-Dbin_contrib=false",
        ]
