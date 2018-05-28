import os
import subprocess

from .base_toolchain import Toolchain
from kiwixbuild.dependencies import GitClone
from kiwixbuild.utils import which
pj = os.path.join

class armhf_toolchain(Toolchain):
    name = 'armhf'

    class Source(GitClone):
        git_remote = "https://github.com/raspberrypi/tools"
        git_dir = "raspberrypi-tools"
