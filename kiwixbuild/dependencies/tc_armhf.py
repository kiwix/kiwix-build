from .base import Dependency, ReleaseDownload, TcCopyBuilder
from kiwixbuild.utils import Remotefile
import os

# The arm toolchains
# This is based on toolchains published here : https://github.com/tttapa/docker-arm-cross-toolchain

base_url = (
    "https://github.com/tttapa/docker-arm-cross-toolchain/releases/download/1.1.0/"
)


class armv6_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "armv6"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "x-tools-armv6-rpi-linux-gnueabihf-gcc12.tar.xz",
            "64f55e89efd36006877e0b218a8a277101603a87b4e52328f66b96c74aa405c6",
            base_url + "x-tools-armv6-rpi-linux-gnueabihf-gcc12.tar.xz",
        )

    class Builder(TcCopyBuilder):
        src_subdir = "armv6-rpi-linux-gnueabihf"


class armv8_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "armv8"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "x-tools-armv8-rpi3-linux-gnueabihf-gcc12.tar.xz",
            "c883ea7c14da5bfb6313a302724d860315be99915126d47023b15437ccea7857",
            base_url + "x-tools-armv8-rpi3-linux-gnueabihf-gcc12.tar.xz",
        )

    class Builder(TcCopyBuilder):
        src_subdir = "armv8-rpi3-linux-gnueabihf"


class aarch64_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = "aarch64"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "x-tools-aarch64-rpi3-linux-gnu-gcc12.tar.xz",
            "ff51d9fd7b3c4f57605e4e16944b9342740876ff3c14991a932ffc9611af5776",
            base_url + "x-tools-aarch64-rpi3-linux-gnu-gcc12.tar.xz"
        )

    class Builder(TcCopyBuilder):
        src_subdir = "aarch64-rpi3-linux-gnu"

        def _fix_missing_lib64(self, path):
            full_path = os.path.join(self.build_path, path)
            if not os.path.exists(full_path):
                os.symlink("lib", full_path)

        def build(self):
            super().build()
            self._fix_missing_lib64("aarch64-rpi3-linux-gnu/sysroot/usr/lib64")
            self._fix_missing_lib64("aarch64-rpi3-linux-gnu/sysroot/lib64")
