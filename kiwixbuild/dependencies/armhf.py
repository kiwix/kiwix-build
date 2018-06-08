from .base import Dependency, GitClone, NoopBuilder

class armhf_toolchain(Dependency):
    neutral = True
    name = 'armhf'

    class Source(GitClone):
        git_remote = "https://github.com/raspberrypi/tools"
        git_dir = "raspberrypi-tools"

    Builder = NoopBuilder
