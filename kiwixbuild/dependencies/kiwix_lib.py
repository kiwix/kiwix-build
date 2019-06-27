import shutil, os

from .base import (
    Dependency,
    GitClone,
    MesonBuilder,
    GradleBuilder)
from kiwixbuild.utils import pj, copy_tree
from kiwixbuild._global import option, get_target_step, neutralEnv

class Kiwixlib(Dependency):
    name = "kiwix-lib"

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-lib.git"
        git_dir = "kiwix-lib"

    class Builder(MesonBuilder):
        dependencies = ["pugixml", "libzim", "zlib", "lzma", "libcurl", "icu4c", "mustache"]
        strip_option = ''

        @property
        def configure_option(self):
            if self.buildEnv.platformInfo.build == 'android':
                return '-Dandroid=true'
            if self.buildEnv.platformInfo.build == 'iOS':
                return '-Db_bitcode=true'
            return ''

        @property
        def library_type(self):
            if self.buildEnv.platformInfo.build == 'android':
                return 'shared'
            return super().library_type


class KiwixlibApp(Dependency):
    name = "kiwix-lib-app"

    Source = Kiwixlib.Source

    class Builder(GradleBuilder):
        dependencies = ["kiwix-lib"]
        gradle_target = "assembleRelease"

        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            if not allDeps:
                return super().get_dependencies(platformInfo, allDeps)
            else:
                deps = [('android_{}'.format(arch), 'kiwix-lib')
                    for arch in option('android_arch')]
                return deps

        def _configure(self, context):
            try:
                shutil.rmtree(self.build_path)
            except FileNotFoundError:
                pass
            if not os.path.exists(self.build_path):
                shutil.copytree(pj(self.source_path, 'android-kiwix-lib-publisher'), self.build_path, symlinks=True)
            for arch in option('android_arch'):
                try:
                    kiwix_builder = get_target_step('kiwix-lib', 'android_{}'.format(arch))
                except KeyError:
                    pass
                else:
                    copy_tree(pj(kiwix_builder.buildEnv.install_dir, 'kiwix-lib'),
                              pj(self.build_path, 'kiwixLibAndroid', 'src', 'main'))

#            The ICU dat file should be embedded with the kiwix-lib application
#            but for now it is package with kiwix-android app and use there.
#            We must fix this at a time (before we update the icu version).
#            os.makedirs(
#                pj(self.build_path, 'app', 'src', 'main', 'assets', 'icu'),
#                exist_ok=True)
#            for arch in option('android_arch'):
#                try:
#                    kiwix_builder = get_target_step('kiwix-lib', 'android_{}'.format(arch))
#                except KeyError:
#                    pass
#                else:
#                    shutil.copy2(pj(kiwix_builder.buildEnv.install_dir, 'share', 'icu', '58.2',
#                                    'icudt58l.dat'),
#                                 pj(self.build_path, 'app', 'src', 'main', 'assets',
#                                    'icu', 'icudt58l.dat'))
#                    break
