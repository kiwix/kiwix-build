from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile


base_url = 'https://master.dl.sourceforge.net/project/raspberry-pi-cross-compilers/'

# This is Gcc 10.3.0 and Raspberry Pi 2 and 3 only !
armhf_base_url = base_url + 'Raspberry%20Pi%20GCC%20Cross-Compiler%20Toolchains/Stretch/GCC%2010.3.0/Raspberry%20Pi%202%2C%203/'

class armhf_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armhf'

    class Source(ReleaseDownload):
        archive = Remotefile('cross-gcc-10.3.0-pi_2-3.tar.gz',
                             '6aef31703fb7bfd63065dda7fb525f1f86a0509c4358c57631a51025805278b3',
                             armhf_base_url + 'cross-gcc-10.3.0-pi_2-3.tar.gz')

    Builder = NoopBuilder
