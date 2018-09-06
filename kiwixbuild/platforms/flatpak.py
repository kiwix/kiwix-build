from .base import PlatformInfo
from kiwixbuild._global import option, neutralEnv

class FlatpakPlatformInfo(PlatformInfo):
    name = 'flatpak'
    build = 'flatpak'
    static = ''
    compatible_hosts = ['debian', 'fedora']

    def __str__(self):
        return "flatpak"
