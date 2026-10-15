from typing import ClassVar

from kiwixbuild.utils import Remotefile

from .base import Dependency, MesonBuilder, ReleaseDownload


class Gumbo(Dependency):
    name = "gumbo"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "gumbo-parser-0.13.1.tar.gz",
            "1a054d1e53d556641a6666537247411a77b0c18ef6ad5df23e30d2131676ef81",
            "https://dev.kiwix.org/kiwix-build/gumbo-parser-0.13.1.tar.gz",
        )

    class Builder(MesonBuilder):
        configure_options: ClassVar[list[str]] = ["-Dtests=false"]
        strip_options: ClassVar[list] = []
