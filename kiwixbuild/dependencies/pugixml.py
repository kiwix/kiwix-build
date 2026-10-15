from typing import ClassVar

from kiwixbuild.utils import Remotefile

from .base import Dependency, MesonBuilder, ReleaseDownload


class Pugixml(Dependency):
    name = "pugixml"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "pugixml-1.15.tar.gz",
            "2e094287f58de02047b2ef23122904de0e02e3b4e9d6b44952d087e746b25974",
            "https://dev.kiwix.org/kiwix-build/pugixml-1.15.tar.gz",
        )
        patches: ClassVar[list[str]] = ["pugixml_meson.patch"]

    class Builder(MesonBuilder):
        strip_options: ClassVar[list] = []
