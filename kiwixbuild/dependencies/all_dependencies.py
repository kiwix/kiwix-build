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
        def get_dependencies(cls, platformInfo):
            base_deps = ['zlib', 'lzma', 'xapian-core', 'gumbo', 'pugixml', 'libmicrohttpd', 'libaria2']
            if platformInfo.build != 'native':
                base_deps += ["icu4c_cross-compile"]
                if platformInfo.build != 'win32':
                    base_deps += ["libmagic_cross-compile"]
            else:
                base_deps += ["icu4c", "libmagic"]
            if (platformInfo.build != 'android' and
                neutralEnv('distname') != 'Darwin'):
                base_deps += ['ctpp2c', 'ctpp2']
            if platformInfo.build == 'android':
                base_deps += ['Gradle']

            return base_deps
