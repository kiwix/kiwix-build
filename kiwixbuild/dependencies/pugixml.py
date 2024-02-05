from .base import Dependency, ReleaseDownload, MesonBuilder

from kiwixbuild.utils import Remotefile


class Pugixml(Dependency):
    name = "pugixml"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "pugixml-1.2.tar.gz",
            "0f422dad86da0a2e56a37fb2a88376aae6e931f22cc8b956978460c9db06136b",
        )
        patches = ["pugixml_meson.patch"]
        flatpak_dest = "src"

    class Builder(MesonBuilder):
        build_type = "release"
        strip_options = []
