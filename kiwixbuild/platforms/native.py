from .base import PlatformInfo

from kiwixbuild.utils import pj
from kiwixbuild._global import option


class NativePlatformInfo(PlatformInfo):
    build = 'native'


class NativeDyn(NativePlatformInfo):
    name = 'native_dyn'
    static = False
    compatible_hosts = ['fedora', 'debian', 'Darwin']

class NativeStatic(NativePlatformInfo):
    name = 'native_static'
    static = True
    compatible_hosts = ['fedora', 'debian']

class NativeMixed(NativePlatformInfo):
    name = 'native_mixed'
    static = False
    compatible_hosts =  ['fedora', 'debian']

    def add_targets(self, targetName, targets):
        print(targetName)
        if option('target') == targetName:
            return super().add_targets(targetName, targets)
        else:
            static_platform = self.get_platform('native_static', targets)
            return static_platform.add_targets(targetName, targets)

    def get_fully_qualified_dep(self, dep):
        if isinstance(dep, tuple):
            return dep
        if option('target') == dep:
            return 'native_mixed', dep
        return 'native_static', dep

    def set_env(self, env):
        super().set_env(env)
        static_platform = self.get_platform('native_static')
        static_buildEnv = static_platform.buildEnv
        static_install_dir = static_buildEnv.install_dir
        env['CPPFLAGS'] = " ".join(['-I'+pj(static_install_dir, 'include'), env['CPPFLAGS']])
        env['PATH'] = ':'.join([pj(static_install_dir, 'bin')] + [env['PATH']])
        pkgconfig_path = pj(static_install_dir, static_buildEnv.libprefix, 'pkgconfig')
        env['PKG_CONFIG_PATH'] = ':'.join([env['PKG_CONFIG_PATH'], pkgconfig_path])
