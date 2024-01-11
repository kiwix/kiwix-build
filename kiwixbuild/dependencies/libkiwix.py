import shutil, os

from .base import (
    Dependency,
    GitClone,
    MesonBuilder)
from kiwixbuild.utils import pj, copy_tree
from kiwixbuild._global import option, get_target_step, neutralEnv

class Libkiwix(Dependency):
    name = "libkiwix"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/libkiwix.git"
        git_dir = "libkiwix"
        git_ref = "error_response_i18n"

    class Builder(MesonBuilder):
        dependencies = ["pugixml", "libzim", "zlib", "lzma", "libcurl", "libmicrohttpd", "icu4c", "mustache", "xapian-core"]
        strip_options = []

        @property
        def build_type(self):
            if self.buildEnv.platformInfo.build == "android":
                return "debug"
            return super().build_type

        @property
        def configure_options(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'android':
                yield '-Dstatic-linkage=true'
                yield '-Dwerror=false'
            if platformInfo.build == 'iOS':
                yield '-Db_bitcode=true'
            if platformInfo.name == 'flatpak':
                yield '--wrap-mode=nodownload'
            if platformInfo.mixed and option('target') == 'libkiwix':
                yield "-Dstatic-linkage=true"

        @property
        def library_type(self):
            if self.buildEnv.platformInfo.build == 'android':
                return 'shared'
            return super().library_type
