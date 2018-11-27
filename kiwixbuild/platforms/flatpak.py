from .base import PlatformInfo
from kiwixbuild._global import option, neutralEnv
from kiwixbuild.utils import run_command

class FlatpakPlatformInfo(PlatformInfo):
    name = 'flatpak'
    build = 'flatpak'
    static = ''
    toolchain_names = ['org.kde']
    compatible_hosts = ['debian', 'fedora']

    def __str__(self):
        return "flatpak"

    def set_env(self, env):
        env['FLATPAK_USER_DIR'] = self.buildEnv.build_dir

