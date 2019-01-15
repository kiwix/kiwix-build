from .base import (
    Dependency,
    ReleaseDownload,
    Builder as BaseBuilder)

from kiwixbuild.utils import Remotefile, pj
from shutil import copy2

class Mustache(Dependency):
    name = "mustache"

    class Source(ReleaseDownload):
        archive = Remotefile('Mustache-3.2.1.tar.gz',
                             '0d17298a81c08f12ebc446cdee387268a395d34bb724050fe67d5ce8c4e98b7a',
                             'https://github.com/kainjow/Mustache/archive/v3.2.1.tar.gz')
        patches = ['mustache_virtual_destructor.patch']

    class Builder(BaseBuilder):
        def build(self):
            self.command('copy_header', self._copy_header)

        def _copy_header(self, context):
            context.try_skip(self.build_path)
            copy2(pj(self.source_path, 'mustache.hpp'),
                  pj(self.buildEnv.install_dir, 'include'))

        def set_flatpak_buildsystem(self, module):
            module['buildsystem'] = 'simple'
            module['build-commands'] = ['cp mustache.hpp /app/include']
