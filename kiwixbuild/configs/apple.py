import subprocess
from typing import ClassVar

from kiwixbuild._global import option
from kiwixbuild.dependencies.apple_xcframework import AppleXCFramework
from kiwixbuild.utils import pj, xrun_find

from .base import ConfigInfo, MetaConfigInfo, mixed_mixin

MIN_MACOS_VERSION = "12.0"


class AppleConfigInfo(ConfigInfo):
    static = True
    compatible_hosts: ClassVar[list[str]] = ["Darwin"]
    arch = None
    host = None
    target = None
    sdk_name = None
    min_iphoneos_version = None
    min_macos_version = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._root_path = None

    @property
    def arch_name(self):
        return self.target

    @property
    def root_path(self):
        if self._root_path is None:
            command = f"xcrun --sdk {self.sdk_name} --show-sdk-path"
            output = subprocess.check_output(command, shell=True)  # noqa: S602
            self._root_path = output[:-1].decode()
        return self._root_path

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile(
            "cmake_ios_cross_file.txt", "cmake_cross_file.txt"
        )
        self.buildEnv.meson_crossfile = self._gen_crossfile(
            "meson_ios_cross_file.txt", "meson_cross_file.txt"
        )

    def get_cross_config(self):
        config = {
            "root_path": self.root_path,
            "binaries": self.binaries,
            "exe_wrapper_def": "",
            "extra_libs": [
                "-isysroot",
                self.root_path,
                "-arch",
                self.arch,
                "-target",
                self.target,
            ],
            "extra_cflags": [
                "-isysroot",
                self.root_path,
                "-arch",
                self.arch,
                "-target",
                self.target,
                *(f"-I{include_dir}" for include_dir in self.get_include_dirs()),
            ],
            "host_machine": {
                "system": "Darwin",
                "lsystem": "darwin",
                "cpu_family": self.arch,
                "cpu": self.cpu,
                "endian": "",
                "abi": "",
            },
        }
        if self.min_iphoneos_version:
            config["extra_libs"].append(
                f"-miphoneos-version-min={self.min_iphoneos_version}"
            )
            config["extra_cflags"].append(
                f"-miphoneos-version-min={self.min_iphoneos_version}"
            )
        if self.min_macos_version:
            config["extra_libs"].append(
                f"-mmacosx-version-min={self.min_macos_version}"
            )
            config["extra_cflags"].append(
                f"-mmacosx-version-min={self.min_macos_version}"
            )
        return config

    def get_env(self):
        env = super().get_env()
        cflags = [env["CFLAGS"]]
        if self.min_iphoneos_version:
            cflags.append(f"-miphoneos-version-min={self.min_iphoneos_version}")
        if self.min_macos_version:
            cflags.append(f"-mmacosx-version-min={self.min_macos_version}")
        env["CFLAGS"] = " ".join(cflags)
        return env

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        cflags = [
            f"-isysroot {self.root_path}",
            f"-arch {self.arch}",
            f"-target {self.target}",
            env["CFLAGS"],
        ]
        if self.min_iphoneos_version:
            cflags.append(f"-miphoneos-version-min={self.min_iphoneos_version}")
        env["CFLAGS"] = " ".join(cflags)
        env["CXXFLAGS"] = " ".join(
            [
                env["CFLAGS"],
                "-std=c++11",
                env["CXXFLAGS"],
            ]
        )
        env["LDFLAGS"] = " ".join(
            [
                f" -arch {self.arch}",
                f"-isysroot {self.root_path}",
            ]
        )

    def get_bin_dir(self):
        return [pj(self.root_path, "bin")]

    @property
    def binaries(self):
        return {
            "CC": xrun_find("clang"),
            "CXX": xrun_find("clang++"),
            "AR": xrun_find("ar"),
            "STRIP": xrun_find("strip"),
            "RANLIB": xrun_find("ranlib"),
            "LD": xrun_find("ld"),
            "PKGCONFIG": "pkg-config",
        }

    @property
    def configure_options(self):
        yield f"--host={self.host}"


class IOSConfigBase(AppleConfigInfo):
    build = "ios"
    min_iphoneos_version = "15.0"

    def __str__(self):
        return "ios"


class IOSArm64(IOSConfigBase):
    name = "ios_arm64"
    arch = cpu = "arm64"
    host = "arm-apple-darwin"
    target = "aarch64-apple-ios"
    sdk_name = "iphoneos"


class IOSSimulatorAmd64(IOSConfigBase):
    name = "ios_simulator_x86_64"
    arch = cpu = "x86_64"
    host = "x86_64-apple-darwin"
    target = "x86-apple-ios-simulator"
    sdk_name = "iphonesimulator"


class IOSSimulatorArm64(IOSConfigBase):
    name = "ios_simulator_arm64"
    arch = cpu = "arm64"
    host = "arm-apple-darwin"
    target = "aarch64-apple-ios-simulator"
    sdk_name = "iphonesimulator"


class MacOSConfigBase(AppleConfigInfo):
    build = "macos"
    min_macos_version = MIN_MACOS_VERSION
    sdk_name = "macosx"

    def __str__(self):
        return "macos"


class MacOSArm64(MacOSConfigBase):
    name = "macos_arm64_static"
    arch = cpu = "arm64"
    host = "aarch64-apple-darwin"
    target = "arm64-apple-macos"


class MacOSArm64Mixed(mixed_mixin("macos_arm64_static"), MacOSConfigBase):
    name = "macos_arm64_mixed"
    arch = cpu = "arm64"
    host = "aarch64-apple-darwin"
    target = "arm64-apple-macos"


class MacOSAmd64(MacOSConfigBase):
    name = "macos_x86-64_static"
    arch = cpu = "x86_64"
    host = "x86_64-apple-darwin"
    target = "x86_64-apple-darwin"


class MacOSAmd64Mixed(mixed_mixin("macos_x86-64_static"), MacOSConfigBase):
    name = "macos_x86-64_mixed"
    arch = cpu = "x86_64"
    host = "x86_64-apple-darwin"
    target = "x86_64-apple-darwin"


class IOS(MetaConfigInfo):
    name = "ios_multi"
    compatible_hosts: ClassVar[list[str]] = ["Darwin"]

    @property
    def arch_name(self):
        return self.name

    @property
    def sub_config_names(self):
        return [f"ios_{arch}" for arch in option("ios_arch")]

    def add_targets(self, target_name, targets):
        super().add_targets(target_name, targets)
        return ConfigInfo.add_targets(self, "_ios_fat_lib", targets)

    def __str__(self):
        return self.name


class AppleStaticAll(MetaConfigInfo):
    name = "apple_all_static"
    compatible_hosts: ClassVar[list[str]] = ["Darwin"]

    @property
    def arch_name(self):
        return self.name

    @property
    def sub_config_names(self):
        return AppleXCFramework.sub_config_names

    def add_targets(self, target_name, targets):
        super().add_targets(target_name, targets)
        return ConfigInfo.add_targets(self, "apple_xcframework", targets)

    def __str__(self):
        return self.name
