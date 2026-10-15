from typing import ClassVar

from kiwixbuild._global import get_target_step, neutral_env, option

from .base import Dependency, GitClone, MesonBuilder


class Libzim(Dependency):
    name = "libzim"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    class Builder(MesonBuilder):
        test_options: ClassVar[list[str]] = ["-t", "8"]
        strip_options: ClassVar[list] = []

        @property
        def build_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "debug"
            return super().build_type

        @classmethod
        def get_dependencies(cls, config_info, _all_deps):
            if neutral_env("distname") == "Windows":
                return ["zstd", "xapian-core", "icu4c", "zim-testing-suite"]
            deps = ["lzma", "zstd", "xapian-core", "icu4c"]
            if config_info.name not in ("flatpak", "wasm"):
                deps.append("zim-testing-suite")
            return deps

        @property
        def configure_options(self):
            config_info = self.buildEnv.configInfo
            if config_info.build in ("android", "wasm"):
                yield "-Dwithout_writer=true"
            if neutral_env("distname") == "Windows":
                yield "-Dwerror=false"
            if config_info.build == "android":
                yield "-DUSE_BUFFER_HEADER=false"
                yield "-Dstatic-linkage=true"
            if config_info.mixed and option("target") == "libzim":
                yield "-Dstatic-linkage=true"
            if config_info.name == "flatpak":
                yield "--wrap-mode=nodownload"
                yield "-Dtest_data_dir=none"
            if config_info.name == "wasm":
                yield "-Dexamples=false"
                yield "-DUSE_MMAP=false"
            if config_info.name not in ("flatpak", "wasm"):
                zim_testing_suite = get_target_step("zim-testing-suite", "source")
                yield f"-Dtest_data_dir={zim_testing_suite.source_path}"

        @property
        def library_type(self):
            if self.buildEnv.configInfo.build == "android":
                return "shared"
            return super().library_type
