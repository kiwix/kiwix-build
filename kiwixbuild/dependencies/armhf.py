from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile

class armhf_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armhf'

    class Source(ReleaseDownload):
        archive = Remotefile('cross-gcc-10.3.0-pi_64.tar.gz',
                             '82bf781d0cf6e4e4809a86c402e1a1dd4de70ed54cff66197ca5a244d4ae5144',
                             'https://deac-ams.dl.sourceforge.net/project/raspberry-pi-cross-compilers/Bonus%20Raspberry%20Pi%20GCC%2064-Bit%20Toolchains/Raspberry%20Pi%20GCC%2064-Bit%20Cross-Compiler%20Toolchains/Bullseye/GCC%2010.3.0/cross-gcc-10.3.0-pi_64.tar.gz',
                             )

    Builder = NoopBuilder
