import os

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
)

from kiwixbuild.utils import Remotefile, pj, Defaultdict, SkipCommand, run_command
from kiwixbuild._global import get_target_step

class LibCurl(Dependency):
    name = "libcurl"

    class Source(ReleaseDownload):
        name = "libcurl"
        archive = Remotefile('curl-7.61.0.tar.xz',
                             'ef6e55192d04713673b4409ccbcb4cb6cd723137d6e10ca45b0c593a454e1720',
                             'https://curl.haxx.se/download/curl-7.61.0.tar.xz')

    Builder = MakeBuilder
