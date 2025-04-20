from .base import Dependency, ReleaseDownload, Builder as BaseBuilder

from kiwixbuild.utils import Remotefile, pj
from shutil import copy2


class Mustache(Dependency):
    name = "mustache"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "Mustache-4.1.tar.gz",
            "acd66359feb4318b421f9574cfc5a511133a77d916d0b13c7caa3783c0bfe167",
            "https://dev.kiwix.org/kiwix-build/mustache-4.1.tar.gz",
        )

    class Builder(BaseBuilder):
        def build(self):
            self.command("copy_header", self._copy_header)

        def _copy_header(self, context):
            context.try_skip(self.build_path)
            copy2(
                pj(self.source_path, "mustache.hpp"),
                pj(self.buildEnv.install_dir, "include"),
            )

        def set_flatpak_buildsystem(self, module):
            module["buildsystem"] = "simple"
            module["build-commands"] = ["cp mustache.hpp /app/include"]
