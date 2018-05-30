import shutil, os

from .base import (
    Dependency,
    GitClone,
    GradleBuilder)

from kiwixbuild.utils import pj
from kiwixbuild._global import option

class KiwixAndroid(Dependency):
    name = "kiwix-android"

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-android"
        git_dir = "kiwix-android"

    class Builder(GradleBuilder):
        dependencies = ["kiwix-lib"]

        def build(self):
            if option('targets') == 'kiwix-android-custom':
                print("SKIP")
            else:
                super().build()

        def _configure(self, context):
            if not os.path.exists(self.build_path):
                shutil.copytree(self.source_path, self.build_path, symlinks=True)
            try:
                shutil.rmtree(pj(self.build_path, 'kiwixlib', 'src', 'main'))
            except FileNotFoundError:
                pass
            shutil.copytree(pj(self.buildEnv.install_dir, 'kiwix-lib'),
                            pj(self.build_path, 'kiwixlib', 'src', 'main'))
            os.makedirs(
                pj(self.build_path, 'app', 'src', 'main', 'assets', 'icu'),
                exist_ok=True)
            shutil.copy2(pj(self.buildEnv.install_dir, 'share', 'icu', '58.2',
                            'icudt58l.dat'),
                         pj(self.build_path, 'app', 'src', 'main', 'assets',
                            'icu', 'icudt58l.dat'))
