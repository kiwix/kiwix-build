from typing import ClassVar

from kiwixbuild.utils import Remotefile

from .base import Dependency, MakeBuilder, ReleaseDownload


class UUID(Dependency):
    name = "uuid"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "e2fsprogs-1.47.3.tar.xz",
            "857e6ef800feaa2bb4578fbc810214be5d3c88b072ea53c5384733a965737329",
            # "https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v1.47.3/e2fsprogs-1.47.3.tar.xz",
        )
        extract_dir = "e2fsprogs-libs-1.47.3"

    class Builder(MakeBuilder):
        configure_options: ClassVar[list[str]] = [
            "--enable-libuuid",
            "--disable-debugfs",
            "--disable-imager",
            "--disable-resizer",
            "--disable-defrag",
            "--enable-fsck",
            "--disable-uuidd",
            "--enable-subset",
        ]
        configure_env: ClassVar[dict[str, str]] = {
            "_format_CFLAGS": "{env.CFLAGS} -O3 -fPIC -Wno-error=implicit-function-declaration"
        }
        static_configure_options: ClassVar[list[str]] = []
        dynamic_configure_options: ClassVar[list[str]] = static_configure_options
        make_targets: ClassVar[list[str]] = ["libs"]
        make_install_targets: ClassVar[list[str]] = ["install-libs"]
