from os import environ

from .base import Dependency, NoopSource, NoopBuilder

from kiwixbuild._global import neutralEnv


class AllBaseDependencies(Dependency):
    name = "alldependencies"

    Source = NoopSource

    class Builder(NoopBuilder):
        @classmethod
        def get_dependencies(cls, configInfo, allDeps):
            if configInfo.build == "wasm" or environ.get("OS_NAME") == "manylinux":
                return ["zlib", "lzma", "zstd", "icu4c", "xapian-core"]

            if neutralEnv("distname") == "Windows":
                base_deps = [
                    "zlib",
                    "zstd",
                    "xapian-core",
                    "zim-testing-suite",
                    "icu4c",
                    "boostregex",
                    "docoptcpp",
                ]

                if not configInfo.name.endswith("_dyn"):
                    base_deps += [
                        "pugixml",
                        "libcurl",
                        "mustache",
                        "libmicrohttpd",
                    ]
            else:
                base_deps = [
                    "zlib",
                    "lzma",
                    "zstd",
                    "xapian-core",
                    "pugixml",
                    "libcurl",
                    "icu4c",
                    "mustache",
                    "libmicrohttpd",
                    "zim-testing-suite",
                ]
                # Add specific dependencies depending of the config
                if configInfo.build not in ("android", "ios"):
                    # For zimtools
                    base_deps += ["docoptcpp", "libmagic", "gumbo"]
                    if (
                        configInfo.build == "native"
                        and neutralEnv("distname") != "Darwin"
                    ):
                        # We compile kiwix-desktop only on native and not on `Darwin`
                        # So we need aria2 only there
                        base_deps += ["aria2"]
            return base_deps
