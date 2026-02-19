from .base import Dependency, ReleaseDownload, MesonBuilder

from kiwixbuild.utils import Remotefile


class zstd(Dependency):
    name = "zstd"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zstd-1.5.7.tar.gz",
            "eb33e51f49a15e023950cd7825ca74a4a2b43db8354825ac24fc1b7ee09e6fa3",
            "https://dev.kiwix.org/kiwix-build/zstd-1.5.7.tar.gz",
        )

        patches = [
            "zstd_qsort.patch",
        ]

    class Builder(MesonBuilder):
        subsource_dir = "build/meson"
        build_type = "release"
        strip_options = []
        configure_options = ["-Dbin_programs=false", "-Dbin_contrib=false"]
