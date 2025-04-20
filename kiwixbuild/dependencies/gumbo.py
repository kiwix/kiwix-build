from .base import Dependency, ReleaseDownload, MakeBuilder

from kiwixbuild.utils import Remotefile, run_command


class Gumbo(Dependency):
    name = "gumbo"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "gumbo-parser-0.12.1.tar.gz",
            "c0bb5354e46539680724d638dbea07296b797229a7e965b13305c930ddc10d82",
            "https://dev.kiwix.org/kiwix-build/gumbo-parser-0.12.1.tar.gz",
        )

        def _post_prepare_script(self, context):
            context.try_skip(self.extract_path)
            command = ["./autogen.sh"]
            run_command(command, self.extract_path, context)

    Builder = MakeBuilder
