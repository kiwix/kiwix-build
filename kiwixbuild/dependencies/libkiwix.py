import shutil, os

from .base import Dependency, GitClone, MesonBuilder
from kiwixbuild.utils import pj, copy_tree
from kiwixbuild._global import option, get_target_step, neutralEnv


class Libkiwix(Dependency):
    name = "libkiwix"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/libkiwix.git"
        git_dir = "libkiwix"

    class Builder(MesonBuilder):
        dependencies = [
            "pugixml",
            "libzim",
            "zlib",
            "lzma",
            "libcurl",
            "libmicrohttpd",
            "icu4c",
            "mustache",
            "xapian-core",
        ]
        strip_options = []

        @property
        def build_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "debug"
            return super().build_type

        @property
        def configure_options(self):
            configInfo = self.buildEnv.configInfo
            if configInfo.build == "android":
                yield "-Dstatic-linkage=true"
                yield "-Dwerror=false"
            if configInfo.build == "iOS":
                yield "-Db_bitcode=true"
            if configInfo.name == "flatpak":
                yield "--wrap-mode=nodownload"
            if configInfo.mixed and option("target") == "libkiwix":
                yield "-Dstatic-linkage=true"

        @property
        def library_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "shared"
            return super().library_type
