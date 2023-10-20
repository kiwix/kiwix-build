from .base import Dependency, ReleaseDownload, TcCopyBuilder
from kiwixbuild.utils import Remotefile

# The arm toolchains
# This is based on toolchains published here : https://github.com/tttapa/docker-arm-cross-toolchain

base_url = "https://github.com/tttapa/docker-arm-cross-toolchain/releases/download/0.1.0/"


aarch_base_url = 'https://master.dl.sourceforge.net/project/raspberry-pi-cross-compilers/Bonus%20Raspberry%20Pi%20GCC%2064-Bit%20Toolchains/Raspberry%20Pi%20GCC%2064-Bit%20Cross-Compiler%20Toolchains/Stretch/GCC%206.3.0/'

class armv6_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armv6'

    class Source(ReleaseDownload):
        archive = Remotefile('x-tools-armv6-rpi-linux-gnueabihf.tar.xz',
                             '4c371c4c5b55ebd1f3d7dd26b14703632d9ba47423f901bcd9303d83ad444434',
                             base_url + 'x-tools-armv6-rpi-linux-gnueabihf.tar.xz')


    class Builder(TcCopyBuilder):
        src_subdir = "armv6-rpi-linux-gnueabihf"


class armv8_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armv8'

    class Source(ReleaseDownload):
        archive = Remotefile('x-tools-armv8-rpi-linux-gnueabihf.tar.xz',
                             'cc28f5c3f6a3e7d9985f98779c4e72224b4eb5a7e4dc2bcdefd90cb241fb94a5',
                             base_url + 'x-tools-armv8-rpi3-linux-gnueabihf.tar.xz')

    class Builder(TcCopyBuilder):
        src_subdir = "armv8-rpi3-linux-gnueabihf"

class aarch64_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "aarch64"

    class Source(ReleaseDownload):
        archive = Remotefile('cross-gcc-6.3.0-pi_64.tar.gz',
                             '1b048bb8886ad63d21797cd9129fc37b9ea0dfaac7e3c36f888aa16fbec1d320',
                             aarch_base_url + 'cross-gcc-6.3.0-pi_64.tar.gz')

    Builder = TcCopyBuilder
