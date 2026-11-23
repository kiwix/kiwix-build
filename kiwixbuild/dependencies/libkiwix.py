from typing import ClassVar

from kiwixbuild._global import option

from .base import Dependency, GitClone, MesonBuilder


class Libkiwix(Dependency):
    name = "libkiwix"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/libkiwix.git"
        git_dir = "libkiwix"

    class Builder(MesonBuilder):
        dependencies: ClassVar[list[str]] = [
            "pugixml",
            "libzim",
            "zlib",
            "libcurl",
            "libmicrohttpd",
            "icu4c",
            "mustache",
            "xapian-core",
        ]
        strip_options: ClassVar[list] = []

        @property
        def build_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "debug"
            return super().build_type

        @property
        def configure_options(self):
            config_info = self.buildEnv.configInfo
            if config_info.build == "android":
                yield "-Dstatic-linkage=true"
                yield "-Dwerror=false"
            if config_info.build in ("ios", "macos"):
                yield "-Db_bitcode=true"
            if config_info.name == "flatpak":
                yield "--wrap-mode=nodownload"
            if config_info.mixed and option("target") == "libkiwix":
                yield "-Dstatic-linkage=true"

        @property
        def library_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "shared"
            return super().library_type
