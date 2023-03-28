from .base import PlatformInfo, MixedMixin

from kiwixbuild.utils import pj
from kiwixbuild._global import option, neutralEnv


class NativePlatformInfo(PlatformInfo):
    build = 'native'

    def get_env(self):
        env = super().get_env()
        if neutralEnv('distname') == 'fedora':
            env['QT_SELECT'] = "5-64"
        return env


class NativeDyn(NativePlatformInfo):
    name = 'native_dyn'
    static = False
    compatible_hosts = ['fedora', 'debian', 'Darwin']

class NativeStatic(NativePlatformInfo):
    name = 'native_static'
    static = True
    compatible_hosts = ['fedora', 'debian']

class NativeMixed(MixedMixin('native_static'), NativePlatformInfo):
    name = 'native_mixed'
    static = False
    compatible_hosts = ['fedora', 'debian', 'Darwin']
