import os
import shutil
from pathlib import Path

from kiwixbuild.configs import ConfigInfo
from kiwixbuild.utils import pj, run_command
from .base import Dependency, NoopSource, Builder as BaseBuilder


class AppleXCFramework(Dependency):
    name = "apple_xcframework"

    macos_subconfigs = (
        "macos_x86-64_static",
        "macos_arm64_static",
    )

    ios_subconfigs = (
        "ios_arm64",
    )

    iossimulator_subconfigs = (
        "ios_simulator_x86_64",
        "ios_simulator_arm64",
    )

    subConfigNames = macos_subconfigs + ios_subconfigs + iossimulator_subconfigs

    Source = NoopSource

    class Builder(BaseBuilder):
        @property
        def all_subconfigs(self):
            return self.buildEnv.configInfo.subConfigNames

        @classmethod
        def get_dependencies(cls, configInfo, alldeps):
            return [(target, "libkiwix") for target in AppleXCFramework.subConfigNames]

        @property
        def final_path(self):
            return pj(self.buildEnv.install_dir, "lib", "CoreKiwix.xcframework")

        def _remove_if_exists(self, context):
            if not os.path.exists(self.final_path):
                return

            shutil.rmtree(self.final_path)

        def _merge_libs(self, context):
            """create merged.a in all targets to bundle all static archives"""
            xcf_libs = []
            for target in self.all_subconfigs:
                static_ars = []

                cfg = ConfigInfo.get_config(target)
                lib_dir = pj(cfg.buildEnv.install_dir, "lib")
                static_ars = [str(f) for f in Path(lib_dir).glob("*.a")]

                # create merged.a from all *.a in install_dir/lib
                command = ["libtool", "-static", "-o", "merged.a", *static_ars]
                run_command(command, lib_dir, context)

                # will be included in xcframework
                if target in AppleXCFramework.ios_subconfigs:
                    # ios subconfigs build libzim without the writer (see #946),
                    # so their header set is smaller than macos's - pair this
                    # library with its own headers, not a shared reference one.
                    headers_dir = pj(cfg.buildEnv.install_dir, "include")
                    xcf_libs.append((pj(lib_dir, "merged.a"), headers_dir))

            return xcf_libs

        def make_fat_with(self, configs, folder_name, context):
            """create fat merged.a in {folder_name} install/lib with {configs}"""
            libs = []
            for target in configs:
                cfg = ConfigInfo.get_config(target)
                libs.append(pj(cfg.buildEnv.install_dir, "lib", "merged.a"))

            fat_dir = pj(self.buildEnv.build_dir, folder_name)
            os.makedirs(fat_dir, exist_ok=True)

            output_merged = pj(fat_dir, "merged.a")
            command = ["lipo", "-create", "-output", output_merged, *libs]
            run_command(command, self.buildEnv.build_dir, context)

            # All configs merged into one fat lib share the same header set
            # (same build type - e.g. all macos, or all ios-simulator), so any
            # one of them is a valid header source for the fat lib.
            headers_dir = pj(
                ConfigInfo.get_config(configs[0]).buildEnv.install_dir, "include"
            )
            return [(output_merged, headers_dir)]

        def _build_xcframework(self, xcf_libs, context):
            # create xcframework
            command = ["xcodebuild", "-create-xcframework"]
            for lib, headers_dir in xcf_libs:
                command += [
                    "-library",
                    lib,
                    "-headers",
                    headers_dir,
                ]
            command += ["-output", self.final_path]
            run_command(command, self.buildEnv.build_dir, context)

        def build(self):
            xcf_libs = []
            self.command("remove_if_exists", self._remove_if_exists)
            xcf_libs += self.command("merge_libs", self._merge_libs)
            xcf_libs += self.command(
                "make_macos_fat",
                self.make_fat_with,
                AppleXCFramework.macos_subconfigs,
                "macos_fat",
            )
            xcf_libs += self.command(
                "make_simulator_fat",
                self.make_fat_with,
                AppleXCFramework.iossimulator_subconfigs,
                "ios-simulator_fat",
            )
            self.command("build_xcframework", self._build_xcframework, xcf_libs)
