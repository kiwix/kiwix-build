import subprocess

from kiwixbuild._global import option
from kiwixbuild.utils import pj, xrun_find
from .base import ConfigInfo, MetaConfigInfo, MixedMixin
from kiwixbuild.dependencies.apple_xcframework import AppleXCFramework


MIN_MACOS_VERSION = "12.0"


class AppleConfigInfo(ConfigInfo):
    build = "iOS"
    static = True
    compatible_hosts = ["Darwin"]
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
            command = "xcrun --sdk {} --show-sdk-path".format(self.sdk_name)
            self._root_path = subprocess.check_output(command, shell=True)[:-1].decode()
        return self._root_path

    def __str__(self):
        return "iOS"

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
                *(
                    "-I{}".format(include_dir)
                    for include_dir in self.get_include_dirs()
                ),
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
                "-miphoneos-version-min={}".format(self.min_iphoneos_version)
            )
            config["extra_cflags"].append(
                "-miphoneos-version-min={}".format(self.min_iphoneos_version)
            )
        if self.min_macos_version:
            config["extra_libs"].append(
                "-mmacosx-version-min={}".format(self.min_macos_version)
            )
            config["extra_cflags"].append(
                "-mmacosx-version-min={}".format(self.min_macos_version)
            )
        return config

    def get_env(self):
        env = super().get_env()
        cflags = [env["CFLAGS"]]
        if self.min_iphoneos_version:
            cflags.append("-miphoneos-version-min={}".format(self.min_iphoneos_version))
        if self.min_macos_version:
            cflags.append("-mmacosx-version-min={}".format(self.min_macos_version))
        env["CFLAGS"] = " ".join(cflags)
        return env

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        cflags = [
            "-isysroot {}".format(self.root_path),
            "-arch {}".format(self.arch),
            "-target {}".format(self.target),
            env["CFLAGS"],
        ]
        if self.min_iphoneos_version:
            cflags.append("-miphoneos-version-min={}".format(self.min_iphoneos_version))
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
                " -arch {}".format(self.arch),
                "-isysroot {}".format(self.root_path),
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


class iOSArm64(AppleConfigInfo):
    name = "ios_arm64"
    arch = cpu = "arm64"
    host = "arm-apple-darwin"
    target = "aarch64-apple-ios"
    sdk_name = "iphoneos"
    min_iphoneos_version = "15.0"


class iOSx64Simulator(AppleConfigInfo):
    name = "iossimulator_x86_64"
    arch = cpu = "x86_64"
    host = "x86_64-apple-darwin"
    target = "x86-apple-ios-simulator"
    sdk_name = "iphonesimulator"
    min_iphoneos_version = "15.0"


class iOSArm64Simulator(AppleConfigInfo):
    name = "iossimulator_arm64"
    arch = cpu = "arm64"
    host = "arm-apple-darwin"
    target = "aarch64-apple-ios-simulator"
    sdk_name = "iphonesimulator"
    min_iphoneos_version = "15.0"


class macOSArm64(AppleConfigInfo):
    name = "macos_arm64_static"
    arch = cpu = "arm64"
    host = "aarch64-apple-darwin"
    target = "arm64-apple-macos"
    sdk_name = "macosx"
    min_iphoneos_version = None
    min_macos_version = MIN_MACOS_VERSION


class macOSArm64Mixed(MixedMixin("macos_arm64_static"), AppleConfigInfo):
    name = "macos_arm64_mixed"
    arch = cpu = "arm64"
    host = "aarch64-apple-darwin"
    target = "arm64-apple-macos"
    sdk_name = "macosx"
    min_iphoneos_version = None
    min_macos_version = MIN_MACOS_VERSION


class macOSx64(AppleConfigInfo):
    name = "macos_x86_64"
    arch = cpu = "x86_64"
    host = "x86_64-apple-darwin"
    target = "x86_64-apple-macos"
    sdk_name = "macosx"
    min_iphoneos_version = None
    min_macos_version = MIN_MACOS_VERSION


class IOS(MetaConfigInfo):
    name = "ios_multi"
    compatible_hosts = ["Darwin"]

    @property
    def arch_name(self):
        return self.name

    @property
    def subConfigNames(self):
        return ["ios_{}".format(arch) for arch in option("ios_arch")]

    def add_targets(self, targetName, targets):
        super().add_targets(targetName, targets)
        return ConfigInfo.add_targets(self, "_ios_fat_lib", targets)

    def __str__(self):
        return self.name


class AppleStaticAll(MetaConfigInfo):
    name = "apple_all_static"
    compatible_hosts = ["Darwin"]

    @property
    def arch_name(self):
        return self.name

    @property
    def subConfigNames(self):
        return AppleXCFramework.subConfigNames

    def add_targets(self, targetName, targets):
        super().add_targets(targetName, targets)
        return ConfigInfo.add_targets(self, "apple_xcframework", targets)

    def __str__(self):
        return self.name
