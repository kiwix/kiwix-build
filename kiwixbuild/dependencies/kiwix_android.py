import shutil, os

from .base import (
    Dependency,
    GitClone,
    GradleBuilder)

from kiwixbuild.utils import pj, copy_tree
from kiwixbuild._global import option, get_target_step

class KiwixAndroid(Dependency):
    name = "kiwix-android"

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-android"
        git_dir = "kiwix-android"

    class Builder(GradleBuilder):
        dependencies = ["kiwix-lib"]

        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            if not allDeps:
                return super().get_dependencies(platformInfo, allDeps)
            else:
                deps = [('android_{}'.format(arch), 'kiwix-lib')
                    for arch in option('android_arch')]
                return deps

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
            for arch in option('android_arch'):
                try:
                    kiwix_builder = get_target_step('kiwix-lib', 'android_{}'.format(arch))
                except KeyError:
                    pass
                else:
                    copy_tree(pj(kiwix_builder.buildEnv.install_dir, 'kiwix-lib'),
                              pj(self.build_path, 'kiwixlib', 'src', 'main'))
            os.makedirs(
                pj(self.build_path, 'app', 'src', 'main', 'assets', 'icu'),
                exist_ok=True)
            for arch in option('android_arch'):
                try:
                    kiwix_builder = get_target_step('kiwix-lib', 'android_{}'.format(arch))
                except KeyError:
                    pass
                else:
                    shutil.copy2(pj(kiwix_builder.buildEnv.install_dir, 'share', 'icu', '58.2',
                                    'icudt58l.dat'),
                                 pj(self.build_path, 'app', 'src', 'main', 'assets',
                                    'icu', 'icudt58l.dat'))
                    break
