from .base import Dependency, ReleaseDownload, MakeBuilder

from kiwixbuild.utils import Remotefile


class lzma(Dependency):
    name = "lzma"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "xz-5.2.6.tar.gz",
            "a2105abee17bcd2ebd15ced31b4f5eda6e17efd6b10f921a01cda4a44c91b3a0",
            "https://altushost-swe.dl.sourceforge.net/project/lzmautils/xz-5.2.6.tar.gz",
        )

    class Builder(MakeBuilder):
        @property
        def configure_options(self):
            return [
                "--disable-xz",
                "--disable-xzdec",
                "--disable-lzmadec",
                "--disable-lzmainfo",
                "--disable-lzma-links",
                "--disable-scripts",
                "--disable-doc",
                #                    "--disable-symbol-versions"
            ]
