from .base import (
    Dependency,
    NoopSource,
    NoopBuilder)

from kiwixbuild._global import neutralEnv

class AllBaseDependencies(Dependency):
    name = "alldependencies"

    Source = NoopSource
    class Builder(NoopBuilder):
        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            base_deps = ['zlib', 'lzma', 'zstd', 'xapian-core', 'pugixml', 'libcurl', 'icu4c', 'mustache', 'libmicrohttpd']
            # zimtools
            # We do not build zimtools at all on "android" and "iOS"
            if platformInfo.build not in ('android', 'iOS'):
                base_deps += ['docoptcpp']
                if platformInfo.build != 'win32':
                    # zimwriterfs
                    base_deps += ['libmagic', 'gumbo']

            return base_deps
