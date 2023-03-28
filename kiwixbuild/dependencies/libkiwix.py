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

    class Builder(MesonBuilder):
        dependencies = ["pugixml", "libzim", "zlib", "lzma", "libcurl", "libmicrohttpd", "icu4c", "mustache", "xapian-core"]
        strip_option = ''

        @property
        def configure_option(self):
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build == 'android':
                return '-Dstatic-linkage=true -Dwerror=false'
            if platformInfo.build == 'iOS':
                return '-Db_bitcode=true'
            if platformInfo.name == 'flatpak':
                return '--wrap-mode=nodownload'
            if platformInfo.mixed and option('target') == 'libkiwix':
                return "-Dstatic-linkage=true"
            return ''

        @property
        def library_type(self):
            if self.buildEnv.platformInfo.build == 'android':
                return 'shared'
            return super().library_type
