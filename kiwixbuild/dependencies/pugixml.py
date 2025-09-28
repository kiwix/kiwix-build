from .base import Dependency, ReleaseDownload, MesonBuilder

from kiwixbuild.utils import Remotefile


class Pugixml(Dependency):
    name = "pugixml"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "pugixml-1.15.tar.gz",
            "2e094287f58de02047b2ef23122904de0e02e3b4e9d6b44952d087e746b25974",
            "https://dev.kiwix.org/kiwix-build/pugixml-1.15.tar.gz"
        )
        patches = ["pugixml_meson.patch"]
        flatpak_dest = "src"

    class Builder(MesonBuilder):
        strip_options = []
