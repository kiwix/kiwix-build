

_fedora_common = ['automake', 'libtool', 'cmake', 'git', 'subversion', 'ccache', 'pkgconfig', 'gcc-c++', 'gettext-devel']
_debian_common = ['automake', 'libtool', 'cmake', 'git', 'subversion', 'ccache', 'pkg-config', 'gcc', 'autopoint']
PACKAGE_NAME_MAPPERS = {
    'flatpak': {
        'zlib': True,
        'lzma': True,
        'icu4c': True,
        'qt': True,
        'qtwebengine': True,
        'uuid': True,
        'libxml2': True,
        'libssl': True,
        'libcurl': True,
    },
    'fedora_native_dyn': {
        'COMMON': _fedora_common,
        'uuid': ['libuuid-devel'],
        'xapian-core': None, # Not the right version on fedora 25
        'pugixml': None, # ['pugixml-devel'] but package doesn't provide pkg-config file
        'libmicrohttpd': ['libmicrohttpd-devel'],
        'zlib': ['zlib-devel'],
        'lzma': ['xz-devel'],
        'icu4c': None,
        'zimlib': None,
        'file' : ['file-devel'],
        'gumbo' : ['gumbo-parser-devel'],
        'aria2': ['aria2'],
    },
    'fedora_native_static': {
        'COMMON': _fedora_common + ['glibc-static', 'libstdc++-static'],
        'zlib': ['zlib-devel', 'zlib-static'],
        'lzma': ['xz-devel', 'xz-static']
        # Either there is no packages, or no static or too old
    },
    'fedora_i586_dyn': {
        'COMMON': _fedora_common + ['glibc-devel.i686', 'libstdc++-devel.i686'],
    },
    'fedora_i586_static': {
        'COMMON': _fedora_common + ['glibc-devel.i686'],
    },
    'fedora_win32_dyn': {
        'COMMON': _fedora_common + ['mingw32-gcc-c++', 'mingw32-bzip2', 'mingw32-win-iconv', 'mingw32-winpthreads', 'wine'],
        'zlib': ['mingw32-zlib'],
        'lzma': ['mingw32-xz-libs'],
        'libmicrohttpd': ['mingw32-libmicrohttpd'],
    },
    'fedora_win32_static': {
        'COMMON': _fedora_common + ['mingw32-gcc-c++', 'mingw32-bzip2-static', 'mingw32-win-iconv-static', 'mingw32-winpthreads-static', 'wine'],
        'zlib': ['mingw32-zlib-static'],
        'lzma': ['mingw32-xz-libs-static'],
        'libmicrohttpd': None, # ['mingw32-libmicrohttpd-static'] packaging dependecy seems buggy, and some static lib are name libfoo.dll.a and
                               # gcc cannot found them.
    },
    'fedora_armhf_static': {
        'COMMON': _fedora_common
    },
    'fedora_armhf_dyn': {
        'COMMON': _fedora_common
    },
    'fedora_android': {
        'COMMON': _fedora_common + ['java-1.8.0-openjdk-devel']
    },
    'debian_native_dyn': {
        'COMMON': _debian_common + ['libbz2-dev', 'libmagic-dev'],
        'zlib': ['zlib1g-dev'],
        'uuid': ['uuid-dev'],
        'libmicrohttpd': ['libmicrohttpd-dev', 'ccache'],
        'qt' : ['libqt5gui5', 'qtbase5-dev', 'qt5-default'],
        'qtwebengine' : ['qtwebengine5-dev'],
        'aria2': ['aria2'],
    },
    'debian_native_static': {
        'COMMON': _debian_common + ['libbz2-dev', 'libmagic-dev'],
        'zlib': ['zlib1g-dev'],
        'uuid': ['uuid-dev'],
    },
    'debian_i586_dyn': {
        'COMMON': _debian_common + ['libc6-dev:i386', 'libstdc++-6-dev:i386', 'gcc-multilib', 'g++-multilib'],
    },
    'debian_i586_static': {
        'COMMON': _debian_common + ['libc6-dev:i386', 'libstdc++-6-dev:i386', 'gcc-multilib', 'g++-multilib'],
    },
    'debian_win32_dyn': {
        'COMMON': _debian_common + ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools'],
    },
    'debian_win32_static': {
        'COMMON': _debian_common + ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools'],
    },
    'debian_armhf_static': {
        'COMMON': _debian_common,
    },
    'debian_armhf_dyn': {
        'COMMON': _debian_common,
    },
    'debian_android': {
        'COMMON': _debian_common + ['default-jdk'],
    },
    'Darwin_native_dyn': {
        'COMMON': ['autoconf', 'automake', 'libtool', 'cmake', 'pkg-config'],
        'file': ['libmagic']
    },
    'Darwin_iOS': {
        'COMMON': ['autoconf', 'automake', 'libtool', 'cmake', 'pkg-config'],
        'file': ['libmagic']
    },
}
