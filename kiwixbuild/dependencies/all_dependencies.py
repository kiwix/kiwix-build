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
            base_deps = ['zlib', 'lzma', 'xapian-core', 'gumbo', 'pugixml', 'libmicrohttpd', 'libaria2', 'icu4c']
            if platformInfo.build != 'win32':
                base_deps += ["libmagic"]
            if (platformInfo.build != 'android' and
                neutralEnv('distname') != 'Darwin'):
                base_deps += ['ctpp2c', 'ctpp2']

            return base_deps
