from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile

class armhf_toolchain(Dependency):
    dont_skip = True
    neutral = True
    name = 'armhf'

    class Source(ReleaseDownload):
        archive = Remotefile('raspberrypi-tools.tar.gz',
                             'e72b35436f2f23f2f7df322d6c318b9be57b21596b5ff0b8936af4ad94e04f2e')

    Builder = NoopBuilder
