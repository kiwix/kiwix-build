from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile


base_url = 'https://master.dl.sourceforge.net/project/raspberry-pi-cross-compilers/'

# This is Gcc 10.3.0 and Raspberry Pi 2 and 3 !
armhf_base_url = base_url + 'Raspberry%20Pi%20GCC%20Cross-Compiler%20Toolchains/Bullseye/GCC%2010.3.0/Raspberry%20Pi%202%2C%203/'

# This is Gcc 10.3.0 and ALL rapsberry Pi arch64
aarch_base_url = base_url + 'Bonus%20Raspberry%20Pi%20GCC%2064-Bit%20Toolchains/Raspberry%20Pi%20GCC%2064-Bit%20Cross-Compiler%20Toolchains/Stretch/GCC%206.3.0/'

class armhf_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armhf'

    class Source(ReleaseDownload):
        archive = Remotefile('bullseyes-cross-gcc-10.3.0-pi_2-3.tar.gz',
                             'c38f7e5c0126312a6b7fd863cd479e0c54844c63640b7b351d3f41a291a0c78e',
                             armhf_base_url + 'cross-gcc-10.3.0-pi_2-3.tar.gz')

    Builder = NoopBuilder


class aarch64_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "aarch64"

    class Source(ReleaseDownload):
        archive = Remotefile('cross-gcc-6.3.0-pi_64.tar.gz',
                             '1b048bb8886ad63d21797cd9129fc37b9ea0dfaac7e3c36f888aa16fbec1d320',
                             aarch_base_url + 'cross-gcc-6.3.0-pi_64.tar.gz')

    Builder = NoopBuilder
