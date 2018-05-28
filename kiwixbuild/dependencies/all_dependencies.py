from .base import (
    Dependency,
    NoopSource,
    NoopBuilder)

from kiwixbuild._global import neutralEnv

class AllBaseDependencies(Dependency):
    name = "alldependencies"

    @property
    def dependencies(self):
        base_deps = ['zlib', 'lzma', 'xapian-core', 'gumbo', 'pugixml', 'libmicrohttpd', 'libaria2']
        if self.buildEnv.platform_info.build != 'native':
            base_deps += ["icu4c_cross-compile"]
            if self.buildEnv.platform_info.build != 'win32':
                base_deps += ["libmagic_cross-compile"]
        else:
            base_deps += ["icu4c", "libmagic"]
        if ( self.buildEnv.platform_info.build != 'android'
           and neutralEnv('distname') != 'Darwin'):
            base_deps += ['ctpp2c', 'ctpp2']
        if self.buildEnv.platform_info.build == 'android':
            base_deps += ['Gradle']

        return base_deps


    Source = NoopSource
    Builder = NoopBuilder
