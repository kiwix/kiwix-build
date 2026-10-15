from typing import ClassVar

from kiwixbuild._global import get_target_step, option
from kiwixbuild.utils import pj

from .base import ConfigInfo, MetaConfigInfo


class AndroidConfigInfo(ConfigInfo):
    build = "android"
    static = True
    toolchain_names: ClassVar[list[str]] = ["android-ndk"]
    compatible_hosts: ClassVar[list[str]] = ["fedora", "debian", "ubuntu"]

    def __str__(self):
        return "android"

    @property
    def libdir(self):
        return f"lib/{self.arch_full}"

    @property
    def binaries_name(self):
        arch_full = self.arch_full
        return {
            "CC": "{}-{}".format(arch_full, "clang"),
            "CXX": "{}-{}".format(arch_full, "clang++"),
            "AR": "llvm-ar",
            "STRIP": "llvm-strip",
            "RANLIB": "llvm-ranlib",
            "LD": "ld",
        }

    def binaries(self):
        install_path = self.install_path
        binaries = {
            k: pj(install_path, "bin", v) for k, v in self.binaries_name.items()
        }
        binaries["PKGCONFIG"] = "pkg-config"
        return binaries

    @property
    def ndk_builder(self):
        return get_target_step("android-ndk", self.name)

    @property
    def install_path(self):
        return self.ndk_builder.install_path

    def get_cross_config(self):
        extra_libs = [
            "-llog",
            "-Wl,--exclude-libs,libgcc.a",
            "-Wl,--exclude-libs,libunwind.a",
            "-Wl,-z,max-page-size=16384",
        ]
        extra_cflags = [f"-I{include_dir}" for include_dir in self.get_include_dirs()]
        if hasattr(self, "march"):
            extra_libs.append(f"-march={self.march}")
            extra_cflags.append(f"-march={self.march}")
        return {
            "exe_wrapper_def": "",
            "install_path": self.install_path,
            "binaries": self.binaries(),
            "root_path": pj(self.install_path, "sysroot"),
            "extra_libs": extra_libs,
            "extra_cflags": extra_cflags,
            "host_machine": {
                "system": "Android",
                "lsystem": "android",
                "cpu_family": self.arch,
                "cpu": self.cpu,
                "endian": "little",
                "abi": self.abi,
            },
        }

    def get_env(self):
        env = super().get_env()
        root_path = pj(self.install_path, "sysroot")
        env["PKG_CONFIG_LIBDIR"] = pj(root_path, "lib", "pkgconfig")
        env["NDK_DEBUG"] = "0"
        return env

    def get_bin_dir(self):
        return [pj(self.install_path, "bin")]

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        root_path = pj(self.install_path, "sysroot")
        march = f"-march={self.march}" if hasattr(self, "march") else ""
        env["CFLAGS"] = (
            f"-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={root_path} {march} "
            + env["CFLAGS"]
        )
        env["CXXFLAGS"] = (
            f"-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={root_path} {march} "
            + env["CXXFLAGS"]
        )
        env["LDFLAGS"] = (
            f"-Wl,-z,max-page-size=16384 --sysroot={root_path} {march} "
            + env["LDFLAGS"]
        )

    def set_compiler(self, env):
        binaries = self.binaries()
        for k, v in binaries.items():
            env[k] = v

    @property
    def configure_options(self):
        yield f"--host={self.arch_full}"

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile(
            "cmake_android_cross_file.txt", "cmake_cross_file.txt"
        )
        self.buildEnv.meson_crossfile = self._gen_crossfile("meson_cross_file.txt")


class AndroidArm(AndroidConfigInfo):
    name = "android_arm"
    arch = cpu = "arm"
    arch_full = "arm-linux-androideabi"
    abi = "armeabi-v7a"
    march = "armv7-a"


class AndroidArm64(AndroidConfigInfo):
    name = "android_arm64"
    arch = "arm64"
    arch_full = "aarch64-linux-android"
    cpu = "aarch64"
    abi = "arm64-v8a"


class AndroidX86(AndroidConfigInfo):
    name = "android_x86"
    arch = abi = "x86"
    arch_full = "i686-linux-android"
    cpu = "i686"


class AndroidX8664(AndroidConfigInfo):
    name = "android_x86_64"
    arch = cpu = abi = "x86_64"
    arch_full = "x86_64-linux-android"


class Android(MetaConfigInfo):
    name = "android"
    compatible_hosts: ClassVar[list[str]] = ["fedora", "debian", "ubuntu"]

    @property
    def arch_name(self):
        return "multi-linux-android"

    @property
    def sub_config_names(self):
        return [f"android_{arch}" for arch in option("android_arch")]

    def add_targets(self, target_name, targets):
        return super().add_targets(target_name, targets)

    def __str__(self):
        return self.name

    def set_comp_flags(self, env):
        pass
