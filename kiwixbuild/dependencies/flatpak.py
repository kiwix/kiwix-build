import os

from .base import Dependency, NoopSource, Builder
from kiwixbuild.utils import Remotefile, add_execution_right, run_command

pj = os.path.join

class org_kde(Dependency):
    neutral = False
    name = 'org.kde'
    version = '5.11'

    Source = NoopSource

    class Builder(Builder):
        def _setup_remote(self, context):
            command = "flatpak --user remote-add --if-not-exists {remote_name} {remote_url}"
            command = command.format(
                remote_name = 'flathub',
                remote_url = 'https://flathub.org/repo/flathub.flatpakrepo'
            )
            run_command(command, self.buildEnv.build_dir, context, buildEnv=self.buildEnv)

        def _install_sdk(self, context):
            command = "flatpak --user install -y {remote_name} {name}.Sdk//{version} {name}.Platform//{version}"
            command = command.format(
                remote_name = 'flathub',
                name = self.target.name,
                version = self.target.version
            )
            run_command(command, self.buildEnv.build_dir, context, buildEnv=self.buildEnv)

        def build(self):
            self.command('setup_remote', self._setup_remote)
            self.command('install_sdk', self._install_sdk)

     
