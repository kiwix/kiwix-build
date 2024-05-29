from .base import Dependency, ReleaseDownload, MakeBuilder

from kiwixbuild.utils import Remotefile


class UUID(Dependency):
    name = "uuid"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "e2fsprogs-libs-1.43.4.tar.gz",
            "0d2e0bf80935c3392b73a60dbff82d8a6ef7ea88b806c2eea964b6837d3fd6c2",
            "https://mirrors.edge.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v1.47.1/e2fsprogs-1.47.1.tar.gz",
        )
        extract_dir = "e2fsprogs-libs-1.47.1"

    class Builder(MakeBuilder):
        configure_options = [
            "--enable-libuuid",
            "--disable-debugfs",
            "--disable-imager",
            "--disable-resizer",
            "--disable-defrag",
            "--enable-fsck",
            "--disable-uuidd",
        ]
        configure_env = {"_format_CFLAGS": "{env.CFLAGS} -O3 -fPIC"}
        static_configure_options = dynamic_configure_options = []
        make_targets = ["libs"]
        make_install_targets = ["install-libs"]
