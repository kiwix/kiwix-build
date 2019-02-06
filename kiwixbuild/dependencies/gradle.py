from .base import (
    Dependency,
    ReleaseDownload,
    Builder as BaseBuilder)

from kiwixbuild.utils import Remotefile, pj, copy_tree, add_execution_right

class Gradle(Dependency):
    neutral = True
    name = "gradle"

    class Source(ReleaseDownload):
        archive = Remotefile('gradle-5.1.1-bin.zip',
                             '4953323605c5d7b89e97d0dc7779e275bccedefcdac090aec123375eae0cc798',
                             'https://services.gradle.org/distributions/gradle-5.1.1-bin.zip')

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
