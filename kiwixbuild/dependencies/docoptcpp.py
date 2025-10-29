from .base import Dependency, ReleaseDownload, MesonBuilder
from kiwixbuild.utils import Remotefile
from kiwixbuild._global import neutralEnv


class DocoptCpp(Dependency):
    name = "docoptcpp"
    version = "0.6.3"  

    class Source(ReleaseDownload):
        src_archive = Remotefile(
            f"v{DocoptCpp.version}.tar.gz",
            "28af5a0c482c6d508d22b14d588a3b0bd9ff97135f99c2814a5aa3cbff1d6632",
            url=f"https://github.com/docopt/docopt.cpp/archive/v{DocoptCpp.version}.tar.gz",
        )

        meson_archive = Remotefile(
            f"docopt_{DocoptCpp.version}-3_patch.zip",
            "1f641187f9d3f35b0a5ebd2011876ef8e9b04b69b7b163095dd7dfa16219ad01",
            url=f"https://wrapdb.mesonbuild.com/v2/docopt_{DocoptCpp.version}-3/get_patch",
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
