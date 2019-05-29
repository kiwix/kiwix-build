import os

from .base import Dependency, ReleaseDownload, NoopBuilder
from kiwixbuild.utils import Remotefile, add_execution_right, run_command

pj = os.path.join

class android_ndk(Dependency):
    neutral = False
    name = 'android-ndk'
    gccver = '4.9.x'

    class Source(ReleaseDownload):
        archive = Remotefile('android-ndk-r19c-linux-x86_64.zip',
                             '4c62514ec9c2309315fd84da6d52465651cdb68605058f231f1e480fcf2692e1',
                             'https://dl.google.com/android/repository/android-ndk-r19c-linux-x86_64.zip')
        @property
        def source_dir(self):
            return self.target.full_name()

    Builder = NoopBuilder
