from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder
)

from kiwixbuild.utils import Remotefile, run_command

class Aria2(Dependency):
    name = "aria2"

    class Source(ReleaseDownload):
        archive = Remotefile('aria2-1.36.0.tar.xz',
                             '58d1e7608c12404f0229a3d9a4953d0d00c18040504498b483305bcb3de907a5',
                             'https://github.com/aria2/aria2/releases/download/release-1.36.0/aria2-1.36.0.tar.xz')

        #def _post_prepare_script(self, context):
        #    context.try_skip(self.extract_path)
        #    command = "autoreconf -i"
        #    run_command(command, self.extract_path, context)

    class Builder(MakeBuilder):
        dependencies = ['zlib']
        configure_option = "--disable-libaria2 --disable-websocket --without-sqlite3"
