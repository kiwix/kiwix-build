import os
from .base import (
    Dependency,
    Builder,
    Source
)
from kiwixbuild.utils import Remotefile, run_command
from kiwixbuild._global import neutralEnv

pj = os.path.join

class VueJs(Dependency):
    name = "vuejs"

    class Source(Source):
        archive = Remotefile('vue.js', '', 'https://vuejs.org/js/vue.js')

        def _download(self, context):
            context.try_skip(neutralEnv('archive_dir'), self.name)
            neutralEnv('download')(self.archive)

        def prepare(self):
            self.command('download', self._download)


    class Builder(Builder):
        def build(self):
            self.command('configure', self._configure)

        def make_dist(self):
            pass

        def _configure(self, context):
            source_path = pj(neutralEnv('archive_dir'), 'vue.js')
            dest_path = pj(neutralEnv('source_dir'), 'kiwix-desktop', 'resources', 'js', 'vue.js')
            if os.path.exists(source_path) and os.path.exists(dest_path):
                os.rename(source_path, dest_path)