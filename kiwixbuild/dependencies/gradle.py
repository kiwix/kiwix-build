from .base import (
    Dependency,
    ReleaseDownload,
    Builder as BaseBuilder)

from kiwixbuild.utils import Remotefile, pj, copy_tree, add_execution_right

class Gradle(Dependency):
    neutral = True
    name = "gradle"

    class Source(ReleaseDownload):
        archive = Remotefile('gradle-5.2-bin.zip',
                             'ff322863250159595e93b5a4d17a6f0d21c59a1a0497c1e1cf1d53826485503f',
                             'https://services.gradle.org/distributions/gradle-5.2-bin.zip')

    class Builder(BaseBuilder):
        @property
        def install_path(self):
            return self.buildEnv.install_dir

        def build(self):
            self.command('install', self._install)

        def _install(self, context):
            copy_tree(
                pj(self.source_path, "bin"),
                pj(self.install_path, "bin"),
                post_copy_function = add_execution_right)
            copy_tree(
                pj(self.source_path, "lib"),
                pj(self.install_path, "lib"))
