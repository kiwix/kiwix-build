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
            base_deps = ['zlib', 'lzma', 'zstd', 'xapian-core', 'pugixml', 'libcurl', 'icu4c', 'mustache', 'libmicrohttpd', 'zim-testing-suite']
            # Add specific dependencies depending of the platform
            if platformInfo.build not in ('android', 'iOS'):
                # For zimtools
                base_deps += ['docoptcpp']
                # For kiwix-desktop
                base_deps += ['aria2']
                if platformInfo.build != 'win32':
                    # zimwriterfs
                    base_deps += ['libmagic', 'gumbo']

            return base_deps
