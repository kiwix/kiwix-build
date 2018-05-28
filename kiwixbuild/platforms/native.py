from .base import PlatformInfo


class NativePlatformInfo(PlatformInfo):
    def __init__(self, name, static, hosts):
        super().__init__(name, 'native', static, [], hosts)


NativePlatformInfo('native_dyn', False, ['fedora', 'debian', 'Darwin'])
NativePlatformInfo('native_static', True, ['fedora', 'debian'])
