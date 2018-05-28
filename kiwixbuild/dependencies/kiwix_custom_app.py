import shutil, os, json
from urllib.parse import urlparse

from .base import (
    Dependency,
    GitClone,
    GradleBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand
from kiwixbuild._global import get_target_step

class KiwixCustomApp(Dependency):
    name = "kiwix-android-custom"

    def __init__(self, buildEnv):
        super().__init__(buildEnv)
        self.custom_name = buildEnv.options.android_custom_app

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-android-custom"
        git_dir = "kiwix-android-custom"

    class Builder(GradleBuilder):
        dependencies = ["kiwix-android", "kiwix-lib"]

        @property
        def gradle_target(self):
            return "assemble{}".format(self.target.custom_name)

        @property
        def gradle_option(self):
            template = ("-i -P customDir={customDir}"
                        " -P zim_file_size={zim_size}"
                        " -P version_code={version_code}"
                        " -P version_name={version_name}"
                        " -P content_version_code={content_version_code}")
            return template.format(
                customDir=pj(self.build_path, 'custom'),
                zim_size=self._get_zim_size(),
                version_code=os.environ['VERSION_CODE'],
                version_name=os.environ['VERSION_NAME'],
                content_version_code=os.environ['CONTENT_VERSION_CODE'])

        @property
        def build_path(self):
            return pj(self.buildEnv.build_dir, "{}_{}".format(self.target.full_name, self.target.custom_name))

        @property
        def custom_build_path(self):
            return pj(self.build_path, 'custom', self.target.custom_name)

        def _get_zim_size(self):
            try:
                zim_size = self.buildEnv.options.zim_file_size
            except AttributeError:
                with open(pj(self.source_path, self.target.custom_name, 'info.json')) as f:
                    app_info = json.load(f)
                zim_size = os.path.getsize(pj(self.custom_build_path, app_info['zim_file']))
            return zim_size

        def build(self):
            self.command('configure', self._configure)
            self.command('download_zim', self._download_zim)
            self.command('compile', self._compile)

        def _download_zim(self, context):
            zim_url = self.buildEnv.options.zim_file_url
            if zim_url is None:
                raise SkipCommand()
            with open(pj(self.source_path, self.target.custom_name, 'info.json')) as f:
                app_info = json.load(f)
            zim_url = app_info.get('zim_url', zim_url)
            out_filename = urlparse(zim_url).path
            out_filename = os.path.basename(out_filename)
            zim_file = Remotefile(out_filename, '', zim_url)
            self.buildEnv.download(zim_file)
            shutil.copy(pj(self.buildEnv.archive_dir, out_filename),
                        pj(self.custom_build_path, app_info['zim_file']))

        def _configure(self, context):
            # Copy kiwix-android in build dir.
            kiwix_android_source = get_target_step('kiwix-android', 'source')
            if not os.path.exists(self.build_path):
                shutil.copytree(kiwix_android_source.source_path, self.build_path)

            # Copy kiwix-lib application in build dir
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

            # Generate custom directory
            try:
                shutil.rmtree(pj(self.build_path, 'custom'))
            except FileNotFoundError:
                pass
            os.makedirs(pj(self.build_path, 'custom'))
            command = "./gen-custom-android-directory.py {custom_name} --output-dir {custom_dir}"
            command = command.format(
                custom_name=self.target.custom_name,
                custom_dir=pj(self.build_path, 'custom', self.target.custom_name)
            )
            self.buildEnv.run_command(command, self.source_path, context)
