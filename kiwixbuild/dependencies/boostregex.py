from .base import Dependency, ReleaseDownload, Builder as BaseBuilder

from kiwixbuild.utils import Remotefile, pj
from shutil import copytree


class BoostRegex(Dependency):
    name = "boostregex"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "regex-boost-1.86.0.zip",
            "",
            "https://codeload.github.com/boostorg/regex/zip/refs/tags/boost-1.86.0",
        )

    class Builder(BaseBuilder):
        def build(self):
            self.command("copy_headers", self._copy_headers)

        def _copy_headers(self, context):
            context.try_skip(self.build_path)
            copytree(
                pj(self.source_path, "include", "boost"),
                pj(self.buildEnv.install_dir, "include", "boost"),
                dirs_exist_ok=True,
            )