import os

from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
)

from kiwixbuild.utils import Remotefile, pj, Defaultdict, SkipCommand
from kiwixbuild._global import get_target_step

class LibMagicBase(Dependency):
    name = "libmagic"

    class Source(ReleaseDownload):
        name = "libmagic"
        source_dir = "libmagic"
        archive = Remotefile('file-5.33.tar.gz',
                             '1c52c8c3d271cd898d5511c36a68059cda94036111ab293f01f83c3525b737c6',
                             'https://fossies.org/linux/misc/file-5.33.tar.gz')

    Builder = MakeBuilder


class LibMagic_native(LibMagicBase):
    name = "libmagic_native"
    force_native_build = True

    class Builder(LibMagicBase.Builder):
        static_configure_option = dynamic_configure_option = "--disable-shared --enable-static"

        @property
        def build_path(self):
            return super().build_path+"_native"

        def _install(self, context):
            raise SkipCommand()


class LibMagic_cross_compile(LibMagicBase):
    name = "libmagic_cross-compile"

    class Builder(LibMagicBase.Builder):
        dependencies = ['libmagic_native']

        def _compile(self, context):
            context.try_skip(self.build_path)
            command = "make -j4 {make_target} {make_option}".format(
                make_target=self.make_target,
                make_option=self.make_option
            )
            libmagic_native_builder = get_target_step('libmagic_native', self.buildEnv.platformInfo.name)
            env = Defaultdict(str, os.environ)
            env['PATH'] = ':'.join([pj(libmagic_native_builder.build_path, 'src'), env['PATH']])
            self.buildEnv.run_command(command, self.build_path, context, env=env)
