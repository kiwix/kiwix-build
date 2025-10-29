from .base import Dependency, ReleaseDownload, MesonBuilder
from kiwixbuild.utils import Remotefile


class Pugixml(Dependency):
    name = "pugixml"
    version = "1.15" 

    class Source(ReleaseDownload):
        archive = Remotefile(
            f"pugixml-{Pugixml.version}.tar.gz", 
            "2e094287f58de02047b2ef23122904de0e02e3b4e9d6b44952d087e746b25974",
            f"https://dev.kiwix.org/kiwix-build/pugixml-{Pugixml.version}.tar.gz", 
        )
        patches = ["pugixml_meson.patch"]

    class Builder(MesonBuilder):
        strip_options = []
