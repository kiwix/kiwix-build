from .base import (
    Dependency,
    ReleaseDownload,
    MakeBuilder,
    Builder as BaseBuilder,
)

from kiwixbuild.utils import pj, SkipCommand, Remotefile, extract_archive
from kiwixbuild._global import get_target_step, neutralEnv
import os, shutil
import fileinput
import platform

if platform.system() == "Windows":

    class Icu(Dependency):
        name = "icu4c"

        class Source(ReleaseDownload):
            archive = Remotefile(
                "icu4c-74_1-Win64-MSVC2022.zip",
                "",
                "https://github.com/unicode-org/icu/releases/download/release-74-1/icu4c-74_1-Win64-MSVC2022.zip",
            )

        class Builder(BaseBuilder):
            def build(self):
                self.command("copy_headers", self._copy_headers)
                self.command("copy_bins", self._copy_bin)
                self.command("generate_pkg_config", self._generate_pkg_config)

            def _copy_headers(self, context):
                context.try_skip(self.build_path)
                shutil.copytree(
                    pj(self.source_path, "include", "unicode"),
                    pj(self.buildEnv.install_dir, "include", "unicode"),
                )

            def _copy_bin(self, context):
                context.try_skip(self.build_path)
                shutil.copytree(
                    pj(self.source_path, "lib64"),
                    pj(self.buildEnv.install_dir, "lib"),
                    dirs_exist_ok=True,
                )

                def ignore_non_dll(path, names):
                    return [n for n in names if not n.endswith(".dll")]

                shutil.copytree(
                    pj(self.source_path, "bin64"),
                    pj(self.buildEnv.install_dir, "bin"),
                    ignore=ignore_non_dll,
                    dirs_exist_ok=True,
                )

            def _generate_pkg_config(self, context):
                context.try_skip(self.build_path)

                pkg_config_template = """ Copyright (C) 2016 and later: Unicode, Inc. and others.
# License & terms of use: http://www.unicode.org/copyright.html
# Copyright (C) 2010-2013, International Business Machines Corporation. All Rights Reserved.

# CFLAGS contains only anything end users should set
CFLAGS = 
# CXXFLAGS contains only anything end users should set
CXXFLAGS =  -std=c++11
# DEFS only contains those UCONFIG_CPPFLAGS which are not auto-set by platform.h
DEFS = 
prefix = {prefix}
exec_prefix = ${{prefix}}
libdir = ${{exec_prefix}}/lib
includedir = ${{prefix}}/include
baselibs = -lpthread -lm 
UNICODE_VERSION=15.0
ICUPREFIX=icu
ICULIBSUFFIX=
LIBICU=lib${{ICUPREFIX}}
pkglibdir=${{libdir}}/icu${{ICULIBSUFFIX}}/73.1
ICUDATA_NAME = icudt73l
ICUDESC=International Components for Unicode

Version: 73.1
Cflags: -I${{includedir}}
Description: International Components for Unicode: Internationalization library
Name: icu-i18n
Libs: -L${{libdir}} -licuin -licuuc -licudt"""

                pkg_config_content = pkg_config_template.format(
                    prefix=self.buildEnv.install_dir
                )

                os.makedirs(
                    pj(self.buildEnv.install_dir, "lib", "pkgconfig"), exist_ok=True
                )
                with open(
                    pj(self.buildEnv.install_dir, "lib", "pkgconfig", "icu-i18n.pc"),
                    mode="w",
                ) as f:
                    f.write(pkg_config_content)

else:

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
                "icu4c_rpath.patch",
                "icu4c_wasm.patch",
            ]

        class Builder(MakeBuilder):
            subsource_dir = "source"
            make_install_targets = ["install"]

            @classmethod
            def get_dependencies(cls, configInfo, allDeps):
                plt = "native_static" if configInfo.static else "native_dyn"
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
                configInfo = self.buildEnv.configInfo
                if configInfo.build != "native":
                    icu_native_builder = get_target_step(
                        "icu4c", "native_static" if configInfo.static else "native_dyn"
                    )
                    yield f"--with-cross-build={icu_native_builder.build_path}"
                    yield "--disable-tools"
                if configInfo.build in ("android", "wasm"):
                    yield "--with-data-packaging=archive"

            def set_env(self, env):
                env["ICU_DATA_FILTER_FILE"] = pj(
                    os.path.dirname(os.path.realpath(__file__)),
                    "icu4c_data_filter.json",
                )

            def _post_configure_script(self, context):
                if self.buildEnv.configInfo.build != "wasm":
                    context.skip()
                context.try_skip(self.build_path)
                for line in fileinput.input(
                    pj(self.build_path, "Makefile"), inplace=True
                ):
                    if line == "#DATASUBDIR = data\n":
                        print("DATASUBDIR = data")
                    else:
                        print(line, end="")
