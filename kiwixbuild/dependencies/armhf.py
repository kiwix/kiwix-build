from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile

# The arm toolchains
# This is based on toolchains published here : https://github.com/tttapa/docker-arm-cross-toolchain

base_url = "https://github.com/tttapa/docker-arm-cross-toolchain/releases/download/0.1.0/"

class armv6_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armv6'

    class Source(ReleaseDownload):
        archive = Remotefile('x-tools-armv6-rpi-linux-gnueabihf.tar.xz',
                             '4c371c4c5b55ebd1f3d7dd26b14703632d9ba47423f901bcd9303d83ad444434',
                             base_url + 'x-tools-armv6-rpi-linux-gnueabihf.tar.xz')

    Builder = NoopBuilder


class armv8_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armv8'

    class Source(ReleaseDownload):
        archive = Remotefile('x-tools-armv8-rpi-linux-gnueabihf.tar.xz',
                             'cc28f5c3f6a3e7d9985f98779c4e72224b4eb5a7e4dc2bcdefd90cb241fb94a5',
                             base_url + 'x-tools-armv8-rpi3-linux-gnueabihf.tar.xz')

    Builder = NoopBuilder

class aarch64_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "aarch64"

    class Source(ReleaseDownload):
        archive = Remotefile('x-tools-aarch64-rpi3-linux-gnu.tar.xz',
                             '8be81d3fc47b1b280bf003646d2b623477badec4ec931944131bf412317b6332',
                             base_url + 'x-tools-aarch64-rpi3-linux-gnu.tar.xz')

    Builder = NoopBuilder
