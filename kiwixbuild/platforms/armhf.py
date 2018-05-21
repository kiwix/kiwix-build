from .base import PlatformInfo


class ArmhfPlatformInfo(PlatformInfo):
    def __init__(self, name, static):
        super().__init__(name, 'armhf', static, ['armhf_toolchain'], ['fedora', 'debian'])

    def get_cross_config(self, host):
        return {
            'extra_libs': [],
            'extra_cflags': [],
            'host_machine': {
                'system': 'linux',
                'lsystem': 'linux',
                'cpu_family': 'arm',
                'cpu': 'armhf',
                'endian': 'little',
                'abi': ''
            }
        }


ArmhfPlatformInfo('armhf_dyn', False)
ArmhfPlatformInfo('armhf_static', True)
