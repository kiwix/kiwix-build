from .base import Dependency, ReleaseDownload, MakeBuilder

from kiwixbuild.utils import Remotefile


class UUID(Dependency):
    name = "uuid"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "e2fsprogs-libs-1.47.3.tar.gz",
            "7d4612f4e4f7ca6c2f669679028bcb02763e3b6280c9c19b2cf168eaf65e88af",
            "https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v1.47.3/e2fsprogs-1.47.3.tar.gz",
        )
        extract_dir = "e2fsprogs-libs-1.47.3"

    class Builder(MakeBuilder):
        configure_options = [
            "--enable-libuuid",
            "--disable-debugfs",
            "--disable-imager",
            "--disable-resizer",
            "--disable-defrag",
            "--enable-fsck",
            "--disable-uuidd",
            "--enable-subset",
        ]
        configure_env = {"_format_CFLAGS": "{env.CFLAGS} -O3 -fPIC -Wno-error=implicit-function-declaration"}
        static_configure_options = dynamic_configure_options = []
        make_targets = ["libs"]
        make_install_targets = ["install-libs"]
