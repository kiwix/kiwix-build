from .base import Dependency, ReleaseDownload, MakeBuilder

from kiwixbuild.utils import Remotefile, run_command


class Gumbo(Dependency):
    name = "gumbo"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "gumbo-parser-0.12.1.tar.gz",
            "ea46815cb6e5c587cc48321dd6a3c3b9071ca605efb19fc1c1735b2cecc0aac6",
            "https://codeberg.org/gumbo-parser/gumbo-parser/archive/master.tar.gz",
        )

    class Builder(MesonBuilder):
        strip_options = []
