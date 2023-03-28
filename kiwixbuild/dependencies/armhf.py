from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile


base_url = 'https://master.dl.sourceforge.net/project/raspberry-pi-cross-compilers/'

# This is Gcc 10.3.0 and Raspberry Pi 2 and 3 only !
armhf_base_url = base_url + 'Raspberry%20Pi%20GCC%20Cross-Compiler%20Toolchains/Stretch/GCC%2010.3.0/Raspberry%20Pi%202%2C%203/'

# This is Gcc 10.3.0 and ALL rapsberry Pi arch64
aarch_base_url = base_url + 'Bonus%20Raspberry%20Pi%20GCC%2064-Bit%20Toolchains/Raspberry%20Pi%20GCC%2064-Bit%20Cross-Compiler%20Toolchains/Stretch/GCC%2010.3.0/'

class armhf_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armhf'

    class Source(ReleaseDownload):
        archive = Remotefile('cross-gcc-10.3.0-pi_2-3.tar.gz',
                             '6aef31703fb7bfd63065dda7fb525f1f86a0509c4358c57631a51025805278b3',
                             armhf_base_url + 'cross-gcc-10.3.0-pi_2-3.tar.gz')

    Builder = NoopBuilder


class aarch64_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "aarch64"

    class Source(ReleaseDownload):
        archive = Remotefile('cross-gcc-10.3.0-pi_64.tar.gz',
                             '5b3fdb7ee8c496c377ab8b11d7ffd404b4d3041f4fdcfeebcbcb734d45a5f3e9',
                             aarch_base_url + 'cross-gcc-10.3.0-pi_64.tar.gz')

    Builder = NoopBuilder
