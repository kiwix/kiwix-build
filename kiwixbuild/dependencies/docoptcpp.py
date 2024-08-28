from .base import Dependency, ReleaseDownload, MesonBuilder

from kiwixbuild.utils import Remotefile
from kiwixbuild._global import neutralEnv

class docoptcpp(Dependency):
    name = "docoptcpp"

    class Source(ReleaseDownload):
        name = "docoptcpp"
        src_archive = Remotefile(
            "v0.6.3.tar.gz",
            "28af5a0c482c6d508d22b14d588a3b0bd9ff97135f99c2814a5aa3cbff1d6632",
            "https://github.com/docopt/docopt.cpp/archive/v0.6.3.tar.gz",
        )

        meson_archive = Remotefile(
            "docopt_0.6.3-3_patch.zip",
            "1f641187f9d3f35b0a5ebd2011876ef8e9b04b69b7b163095dd7dfa16219ad01",
            "https://wrapdb.mesonbuild.com/v2/docopt_0.6.3-3/get_patch",
        )

        archives = [src_archive, meson_archive]
        patches = [
            "docopt_meson_install_pkgconfig.patch",
            "docopt_meson_use_boostregex.patch",
        ]

    class Builder(MesonBuilder):
        @classmethod
        def get_dependencies(cls, configInfo, allDeps):
            if neutralEnv("distname") == "Windows":
                return ["boostregex"]
            return []