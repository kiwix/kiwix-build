from .base import Dependency, ReleaseDownload, MakeBuilder
from kiwixbuild.utils import Remotefile


class UUID(Dependency):
    name = "uuid"
    version = "1.43.4"  

    class Source(ReleaseDownload):
        archive = Remotefile(
            f"e2fsprogs-libs-{UUID.version}.tar.gz",  
            "eed4516325768255c9745e7b82c9d7d0393abce302520a5b2cde693204b0e419",
            f"https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v{UUID.version}/e2fsprogs-libs-{UUID.version}.tar.gz",
        )
        extract_dir = f"e2fsprogs-libs-{UUID.version}" 

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
