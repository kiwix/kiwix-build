from .base import Dependency, ReleaseDownload, MakeBuilder, NoopBuilder

from kiwixbuild.utils import Remotefile, run_command, pj
import platform
from shutil import copy2

# Important: in case of aria2c update,
# 'scripts/create_kiwix-desktop_appImage.sh' should not be forgotten!

class Aria2(Dependency):
    name = "aria2"

    if platform.system() == "Windows":

        class Source(ReleaseDownload):
            archive = Remotefile(
                "aria2-1.37.0-win-64bit-build1.zip",
                "67d015301eef0b612191212d564c5bb0a14b5b9c4796b76454276a4d28d9b288",
                "https://dev.kiwix.org/kiwix-desktop/aria2-1.37.0-win-64bit-build1.zip",
            )

        class Builder(NoopBuilder):
            def build(self):
                self.command("copy_binary", self._copy_binary)

            def _copy_binary(self, context):
                context.try_skip(self.build_path)
                copy2(
                    pj(self.source_path, "aria2c.exe"),
                    pj(self.buildEnv.install_dir, "bin"),
                )

    else:

        class Source(ReleaseDownload):
            archive = Remotefile(
                "aria2-1.37.0.tar.xz",
                "60a420ad7085eb616cb6e2bdf0a7206d68ff3d37fb5a956dc44242eb2f79b66b",
                "https://dev.kiwix.org/kiwix-desktop/aria2-1.37.0.tar.xz",
            )

            def _post_prepare_script(self, context):
                context.try_skip(self.extract_path)
                command = ["autoreconf", "-i"]
                run_command(command, self.extract_path, context)

        class Builder(MakeBuilder):
            dependencies = ["zlib"]
            configure_options = [
                "--disable-libaria2",
                "--disable-websocket",
                "--without-sqlite3",
            ]
