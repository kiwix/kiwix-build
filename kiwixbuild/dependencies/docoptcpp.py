from .base import (
    Dependency,
    ReleaseDownload,
    CMakeBuilder)

from kiwixbuild.utils import Remotefile



class docoptcpp(Dependency):
    name = 'docoptcpp'

    class Source(ReleaseDownload):
        archive = Remotefile('v0.6.2.tar.gz',
                             'c05542245232420d735c7699098b1ea130e3a92bade473b64baf876cdf098a17',
                             'https://github.com/docopt/docopt.cpp/archive/v0.6.2.tar.gz')

    class Builder(CMakeBuilder):
        make_install_target = 'install'

