from .base import Dependency, ReleaseDownload, MakeBuilder

from kiwixbuild.utils import pj, SkipCommand, Remotefile, extract_archive
from kiwixbuild._global import get_target_step, neutralEnv
import os, shutil
import fileinput


class Icu(Dependency):
    name = "icu4c"

    class Source(ReleaseDownload):
        archive_src = Remotefile(
            "icu4c-73_2-src.tgz",
            "818a80712ed3caacd9b652305e01afc7fa167e6f2e94996da44b90c2ab604ce1",
            "https://github.com/unicode-org/icu/releases/download/release-73-2/icu4c-73_2-src.tgz",
        )
        archive_data = Remotefile(
            "icu4c-73_2-data.zip",
            "ca1ee076163b438461e484421a7679fc33a64cd0a54f9d4b401893fa1eb42701",
            "https://github.com/unicode-org/icu/releases/download/release-73-2/icu4c-73_2-data.zip",
        )

        archives = [archive_src, archive_data]

        def _extract(self, context):
            context.try_skip(self.extract_path)
            if os.path.exists(self.extract_path):
                shutil.rmtree(self.extract_path)
            extract_archive(
                pj(neutralEnv("archive_dir"), self.archive_src.name),
                neutralEnv("source_dir"),
                topdir=None,
                name=self.source_dir,
            )
            shutil.rmtree(
                pj(neutralEnv("source_dir"), self.source_dir, "source", "data")
            )
            extract_archive(
                pj(neutralEnv("archive_dir"), self.archive_data.name),
                pj(neutralEnv("source_dir"), self.source_dir, "source"),
                topdir="data",
                name="data",
            )

        patches = [
            "icu4c_fix_static_lib_name_mingw.patch",
            #           "icu4c_android_elf64_st_info.patch",
            #           "icu4c_custom_data.patch",
            #           "icu4c_noxlocale.patch",
            "icu4c_rpath.patch",
            #           "icu4c_build_config.patch",
            "icu4c_wasm.patch",
        ]

    class Builder(MakeBuilder):
        subsource_dir = "source"
        make_install_targets = ["install"]

        @classmethod
        def get_dependencies(cls, platformInfo, allDeps):
            plt = "native_static" if platformInfo.static else "native_dyn"
            return [(plt, "icu4c")]

        @property
        def configure_options(self):
            yield "--disable-samples"
            yield "--disable-tests"
            yield "--disable-extras"
            yield "--disable-dyload"
            yield "--enable-rpath"
            yield "--disable-icuio"
            yield "--disable-layoutex"
            platformInfo = self.buildEnv.platformInfo
            if platformInfo.build != "native":
                icu_native_builder = get_target_step(
                    "icu4c", "native_static" if platformInfo.static else "native_dyn"
                )
                yield f"--with-cross-build={icu_native_builder.build_path}"
                yield "--disable-tools"
            if platformInfo.build in ("android", "wasm"):
                yield "--with-data-packaging=archive"

        def set_env(self, env):
            env["ICU_DATA_FILTER_FILE"] = pj(
                os.path.dirname(os.path.realpath(__file__)), "icu4c_data_filter.json"
            )

        def _post_configure_script(self, context):
            if self.buildEnv.platformInfo.build != "wasm":
                context.skip()
            context.try_skip(self.build_path)
            for line in fileinput.input(pj(self.build_path, "Makefile"), inplace=True):
                if line == "#DATASUBDIR = data\n":
                    print("DATASUBDIR = data")
                else:
                    print(line, end="")
