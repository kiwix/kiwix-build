import os
import shutil
from pathlib import Path

from kiwixbuild.configs import ConfigInfo
from kiwixbuild.utils import pj, run_command
from .base import Dependency, NoopSource, Builder as BaseBuilder


class AppleXCFramework(Dependency):
    name = "apple_xcframework"
    subConfigNames = [
        "macos_x86_64",
        "macos_arm64_static",
        "ios_arm64",
        "iossimulator_x86_64",
        "iossimulator_arm64",
    ]
    Source = NoopSource

    class Builder(BaseBuilder):
        @property
        def all_subconfigs(self):
            return self.buildEnv.configInfo.subConfigNames

        @property
        def macos_subconfigs(self):
            return [
                target for target in self.all_subconfigs if target.startswith("macos")
            ]

        @property
        def iossimulator_subconfigs(self):
            return [
                target
                for target in self.all_subconfigs
                if target.startswith("iossimulator")
            ]

        @property
        def ios_subconfigs(self):
            return [
                target for target in self.all_subconfigs if target.startswith("ios_")
            ]

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
                if target in self.ios_subconfigs:
                    xcf_libs.append(pj(lib_dir, "merged.a"))

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

            return [output_merged]

        def _build_xcframework(self, xcf_libs, context):
            # create xcframework
            ref_conf = ConfigInfo.get_config(self.macos_subconfigs[0])
            command = ["xcodebuild", "-create-xcframework"]
            for lib in xcf_libs:
                command += [
                    "-library",
                    lib,
                    "-headers",
                    pj(ref_conf.buildEnv.install_dir, "include"),
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
                self.macos_subconfigs,
                "macos_fat",
            )
            xcf_libs += self.command(
                "make_simulator_fat",
                self.make_fat_with,
                self.iossimulator_subconfigs,
                "ios-simulator_fat",
            )
            self.command("build_xcframework", self._build_xcframework, xcf_libs)
