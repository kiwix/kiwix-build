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
            # zimwriterfs
            if platformInfo.build not in ('android', 'win32'):
                base_deps += ['libmagic', 'gumbo']
            
            # zimtools
            if platformInfo.build not in ('android','iOS'):
                base_deps += ['docoptcpp']

            return base_deps
