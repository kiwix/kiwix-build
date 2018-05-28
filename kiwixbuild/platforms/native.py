from .base import PlatformInfo


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
