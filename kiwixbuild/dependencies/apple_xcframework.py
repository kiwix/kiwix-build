import os
import shutil
from pathlib import Path

from kiwixbuild.platforms import PlatformInfo
from kiwixbuild.utils import pj, run_command
from .base import Dependency, NoopSource, Builder as BaseBuilder


class AppleXCFramework(Dependency):
    name = "apple_xcframework"
    subPlatformNames = ["macOS_x86_64", "macOS_arm64_static", "iOS_x86_64", "iOS_arm64"]
    Source = NoopSource

    class Builder(BaseBuilder):
        @property
        def all_subplatforms(self):
            return self.buildEnv.platformInfo.subPlatformNames

        @property
        def macos_subplatforms(self):
            return [
                target for target in self.all_subplatforms if target.startswith("macOS")
            ]

        @property
        def ios_subplatforms(self):
            return [
                target for target in self.all_subplatforms if target.startswith("iOS")
            ]

        @classmethod
        def get_dependencies(cls, platfomInfo, alldeps):
            return [
                (target, "libkiwix") for target in AppleXCFramework.subPlatformNames
            ]

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
            for target in self.all_subplatforms:
                static_ars = []

                plt = PlatformInfo.get_platform(target)
                lib_dir = pj(plt.buildEnv.install_dir, "lib")
                static_ars = [str(f) for f in Path(lib_dir).glob("*.a")]

                # create merged.a from all *.a in install_dir/lib
                command = [
                    "libtool",
                    "-static",
                    "-o",
                    "merged.a",
                    *static_ars
                ]
                run_command(command, lib_dir, context)

                # will be included in xcframework
                if target in self.ios_subplatforms:
                    xcf_libs.append(pj(lib_dir, "merged.a"))

            return xcf_libs

        def _make_macos_fat(self, context):
            """create fat merged.a in fake macOS_fat install/lib with macOS archs"""
            macos_libs = []
            for target in self.macos_subplatforms:
                plt = PlatformInfo.get_platform(target)
                macos_libs.append(pj(plt.buildEnv.install_dir, "lib", "merged.a"))

            fat_dir = pj(self.buildEnv.build_dir, "macOS_fat")
            os.makedirs(fat_dir, exist_ok=True)

            output_merged = pj(fat_dir, "merged.a")
            command = [
                "lipo",
                "-create",
                "-output",
                output_merged,
                *macos_libs
            ]
            run_command(command, self.buildEnv.build_dir, context)

            return [output_merged]

        def _build_xcframework(self, xcf_libs, context):
            # create xcframework
            ref_plat = PlatformInfo.get_platform(self.macos_subplatforms[0])
            command = ["xcodebuild", "-create-xcframework"]
            for lib in xcf_libs:
                command += [
                    "-library", lib,
                    "-headers", pj(ref_plat.buildEnv.install_dir, "include")
                ]
            command += ["-output", self.final_path]
            run_command(command, self.buildEnv.build_dir, context)

        def build(self):
            xcf_libs = []
            self.command("remove_if_exists", self._remove_if_exists)
            xcf_libs += self.command("merge_libs", self._merge_libs)
            xcf_libs += self.command("make_macos_fat", self._make_macos_fat)
            self.command("build_xcframework", self._build_xcframework, xcf_libs)
