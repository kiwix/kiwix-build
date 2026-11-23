from kiwixbuild.utils import colorize

from .base import Dependency, NoopBuilder, NoopSource


class Qt(Dependency):
    name = "qt"

    Source = NoopSource

    class Builder(NoopBuilder):
        def build(self):
            error_msg = f"""WARNING: kiwix-build cannot build {self.name} for you.
You must install it yourself using official Qt installer or your distribution system."""
            print(colorize(error_msg, "WARNING"))


class QtWebEngine(Dependency):
    name = "qtwebengine"

    Source = NoopSource

    Builder = Qt.Builder
