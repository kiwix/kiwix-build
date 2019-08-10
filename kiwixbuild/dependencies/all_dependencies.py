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
            base_deps = ['zlib', 'lzma', 'xapian-core', 'pugixml', 'libcurl', 'icu4c', 'mustache', 'libmicrohttpd']
            # zimwriterfs
            if platformInfo.build not in ('android', 'win32'):
                base_deps += ['libmagic', 'gumbo']

            return base_deps
