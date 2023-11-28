from .base import Dependency, ReleaseDownload, MesonBuilder

from kiwixbuild.utils import Remotefile


class zstd(Dependency):
    name = "zstd"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "zstd-1.5.5.tar.gz",
            "98e9c3d949d1b924e28e01eccb7deed865eefebf25c2f21c702e5cd5b63b85e1",
            "https://github.com/facebook/zstd/archive/refs/tags/v1.5.5.tar.gz",
        )

    class Builder(MesonBuilder):
        subsource_dir = "build/meson"
        build_type = "release"
        strip_options = []
        configure_options = ["-Dbin_programs=false", "-Dbin_contrib=false"]
