import os
import shutil

from .base import Dependency, ReleaseDownload, Builder
from kiwixbuild.utils import Remotefile, run_command

pj = os.path.join

class android_sdk(Dependency):
    neutral = True
    name = 'android-sdk'

    class Source(ReleaseDownload):
        archive = Remotefile('tools_r25.2.3-linux.zip',
                             '1b35bcb94e9a686dff6460c8bca903aa0281c6696001067f34ec00093145b560',
                             'https://dl.google.com/android/repository/tools_r25.2.3-linux.zip')

    class Builder(Builder):

        @property
        def install_path(self):
            return pj(self.buildEnv.toolchain_dir, self.target.full_name())

        def _build_platform(self, context):
            context.try_skip(self.install_path)
            tools_dir = pj(self.install_path, 'tools')
            shutil.copytree(self.source_path, tools_dir)
            script = pj(tools_dir, 'android')
            command = '{script} --verbose update sdk -a --no-ui --filter {packages}'
            packages = [
                'tools','platform-tools',
                'build-tools-28.0.3', 'build-tools-27.0.3',
                'android-28', 'android-27'
            ]
            command = command.format(
                script=script,
                packages = ','.join(packages)
            )
            run_command(command, self.install_path, context, input="y\n")

        def _fix_licenses(self, context):
            context.try_skip(self.install_path)
            os.makedirs(pj(self.install_path, 'licenses'), exist_ok=True)
            with open(pj(self.install_path, 'licenses', 'android-sdk-license'), 'w') as f:
                f.write("\n8933bad161af4178b1185d1a37fbf41ea5269c55\nd56f5187479451eabf01fb78af6dfcb131a6481e")

        def build(self):
            self.command('build_platform', self._build_platform)
            self.command('fix_licenses', self._fix_licenses)
