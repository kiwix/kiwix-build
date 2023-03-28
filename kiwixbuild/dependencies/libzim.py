from .base import (
    Dependency,
    GitClone,
    MesonBuilder)
from kiwixbuild._global import option, get_target_step

class Libzim(Dependency):
    name = "libzim"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    class Builder(MesonBuilder):
        test_option = "-t 8"
        strip_option = ''

        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            deps = ['lzma', 'zstd', 'xapian-core', 'icu4c']
            if platformInfo.name not in ('flatpak', 'wasm'):
                deps.append('zim-testing-suite')
            return deps

        @property
        def configure_option(self):
            platformInfo = self.buildEnv.platformInfo
            config_options = []
            if platformInfo.build == 'android':
                config_options.append("-DUSE_BUFFER_HEADER=false")
                config_options.append("-Dstatic-linkage=true")
            if platformInfo.build == 'iOS':
                config_options.append("-Db_bitcode=true")
            if platformInfo.mixed and option('target') == 'libzim':
                config_options.append("-Dstatic-linkage=true")
            if platformInfo.name == "flatpak":
                config_options.append("--wrap-mode=nodownload")
                config_options.append("-Dtest_data_dir=none")
            if platformInfo.name == "wasm":
                config_options.append("-Dexamples=false")
                config_options.append("-DUSE_MMAP=false")
            if platformInfo.name not in ("flatpak", "wasm"):
                zim_testing_suite = get_target_step('zim-testing-suite', 'source')
                config_options.append('-Dtest_data_dir={}'.format(zim_testing_suite.source_path))
            return " ".join(config_options)

        @property
        def library_type(self):
            if self.buildEnv.platformInfo.build == 'android':
                return 'shared'
            return super().library_type
