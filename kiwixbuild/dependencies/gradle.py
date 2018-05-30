from .base import (
    Dependency,
    ReleaseDownload,
    Builder as BaseBuilder)

from kiwixbuild.utils import Remotefile, pj, copy_tree, add_execution_right

class Gradle(Dependency):
    neutral = True
    name = "gradle"

    class Source(ReleaseDownload):
        archive = Remotefile('gradle-4.6-bin.zip',
                             '98bd5fd2b30e070517e03c51cbb32beee3e2ee1a84003a5a5d748996d4b1b915',
                             'https://services.gradle.org/distributions/gradle-4.6-bin.zip')

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
