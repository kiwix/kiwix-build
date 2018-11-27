from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder
)

from kiwixbuild.utils import Remotefile, run_command

class Aria2(Dependency):
    name = "aria2"

    class Source(ReleaseDownload):
        archive = Remotefile('aria2-1.34.0.tar.xz',
                             '3a44a802631606e138a9e172a3e9f5bcbaac43ce2895c1d8e2b46f30487e77a3',
                             'https://github.com/aria2/aria2/releases/download/release-1.34.0/aria2-1.34.0.tar.xz')

        patches = ["libaria2_android.patch"]

        def _post_prepare_script(self, context):
            context.try_skip(self.extract_path)
            command = "autoreconf -i"
            run_command(command, self.extract_path, context)

    class Builder(MakeBuilder):
        dependencies = ['zlib']
        configure_option = "--disable-libaria2 --without-sqlite3"
