from .base import Dependency, GitClone, MesonBuilder
from kiwixbuild._global import option, get_target_step, neutralEnv


class Libzim(Dependency):
    name = "libzim"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    class Builder(MesonBuilder):
        test_options = ["-t", "8"]
        strip_options = []

        @property
        def build_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "debug"
            return super().build_type

        @classmethod
        def get_dependencies(cls, configInfo, allDeps):
            if neutralEnv("distname") == "Windows":
                return ["zstd", "icu4c", "zim-testing-suite"]
            deps = ["lzma", "zstd", "xapian-core", "icu4c"]
            if configInfo.name not in ("flatpak", "wasm"):
                deps.append("zim-testing-suite")
            return deps

        @property
        def configure_options(self):
            configInfo = self.buildEnv.configInfo
            if neutralEnv("distname") == "Windows":
                yield "-Dwith_xapian=false"
            if configInfo.build == "android":
                yield "-DUSE_BUFFER_HEADER=false"
                yield "-Dstatic-linkage=true"
            if configInfo.mixed and option("target") == "libzim":
                yield "-Dstatic-linkage=true"
            if configInfo.name == "flatpak":
                yield "--wrap-mode=nodownload"
                yield "-Dtest_data_dir=none"
            if configInfo.name == "wasm":
                yield "-Dexamples=false"
                yield "-DUSE_MMAP=false"
            if configInfo.name not in ("flatpak", "wasm"):
                zim_testing_suite = get_target_step("zim-testing-suite", "source")
                yield "-Dtest_data_dir={}".format(zim_testing_suite.source_path)

        @property
        def library_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "shared"
            return super().library_type
