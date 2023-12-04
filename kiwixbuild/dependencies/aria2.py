from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder
)

from kiwixbuild.utils import Remotefile, run_command

class Aria2(Dependency):
    name = "aria2"

    class Source(ReleaseDownload):
        archive = Remotefile('aria2-1.37.0.tar.xz',
                             '60a420ad7085eb616cb6e2bdf0a7206d68ff3d37fb5a956dc44242eb2f79b66b',
                             'https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0.tar.xz')

        def _post_prepare_script(self, context):
            context.try_skip(self.extract_path)
            command = ["autoreconf", "-i"]
            run_command(command, self.extract_path, context)

    class Builder(MakeBuilder):
        dependencies = ['zlib']
        configure_options = ["--disable-libaria2", "--disable-websocket", "--without-sqlite3"]
