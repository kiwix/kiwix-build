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
            base_deps = ['zlib', 'lzma', 'xapian-core', 'pugixml', 'libcurl', 'icu4c', 'mustache']
            # zimwriterfs
            if platformInfo.build not in ('android', 'win32'):
                base_deps += ['libmagic', 'gumbo']
            # kiwix-tools
            if (platformInfo.build != 'android' and
                neutralEnv('distname') != 'Darwin'):
                base_deps += ['libmicrohttpd']

            return base_deps
