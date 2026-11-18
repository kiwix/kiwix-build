from .base import Dependency, ReleaseDownload, MesonBuilder

from kiwixbuild.utils import Remotefile


class Gumbo(Dependency):
    name = "gumbo"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "gumbo-parser-0.14.1.tar.gz",
            "ba5d13b9b508ec693613b3b61518163aced38f8e885f7e28dc047348a4e61365",
            "https://dev.kiwix.org/kiwix-build/gumbo-parser-0.14.1.tar.gz", # https://codeberg.org/gumbo-parser/gumbo-parser/releases
        )

    class Builder(MesonBuilder):
        configure_options = [
            "-Dtests=false"
        ]
        strip_options = []
