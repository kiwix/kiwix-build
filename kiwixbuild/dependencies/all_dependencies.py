from os import environ

from .base import Dependency, NoopSource, NoopBuilder

from kiwixbuild._global import neutralEnv


class AllBaseDependencies(Dependency):
    name = "alldependencies"

    Source = NoopSource

    class Builder(NoopBuilder):
        @classmethod
        def get_dependencies(cls, configInfo, allDeps):
            if neutralEnv("distname") == "Windows":
                return ["zlib", "lzma", "zstd", "icu4c"]
            if configInfo.build == "wasm" or environ.get("OS_NAME") == "bionic":
                return ["zlib", "lzma", "zstd", "icu4c", "xapian-core"]

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
            if configInfo.build not in ("android", "iOS"):
                # For zimtools
                base_deps += ["docoptcpp"]
                if configInfo.build != "win32":
                    # zimwriterfs
                    base_deps += ["libmagic", "gumbo"]
                if configInfo.build == "native" and neutralEnv("distname") != "Darwin":
                    # We compile kiwix-desktop only on native and not on `Darwin`
                    # So we need aria2 only there
                    base_deps += ["aria2"]
            return base_deps
