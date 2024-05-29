from .base import ConfigInfo, MixedMixin

from kiwixbuild.utils import pj, get_separator
from kiwixbuild._global import get_target_step


# Base config for arm
class ArmConfigInfo(ConfigInfo):
    compatible_hosts = ["fedora", "debian"]

    def get_cross_config(self):
        return {
            "binaries": self.binaries,
            "exe_wrapper_def": "",
            "root_path": self.root_path,
            "extra_libs": [],
            "extra_cflags": [
                "-I{}".format(include_dir) for include_dir in self.get_include_dirs()
            ],
            "host_machine": {
                "system": "linux",
                "lsystem": "linux",
                "cpu_family": self.cpu_family,
                "cpu": self.cpu,
                "endian": "little",
                "abi": "",
            },
        }

    @property
    def libdir(self):
        return "lib/{}".format(self.arch_full)

    @property
    def toolchain(self):
        return get_target_step(self.build, "neutral")

    @property
    def root_path(self):
        return self.toolchain.build_path

    @property
    def binaries(self):
        binaries = (
            (k, "{}-{}".format(self.arch_full, v))
            for k, v in (
                ("CC", "gcc"),
                ("CXX", "g++"),
                ("AR", "ar"),
                ("STRIP", "strip"),
                ("WINDRES", "windres"),
                ("RANLIB", "ranlib"),
                ("LD", "ld"),
                ("LDSHARED", "g++ -shared"),
            )
        )
        binaries = {k: pj(self.root_path, "bin", v) for k, v in binaries}
        binaries["PKGCONFIG"] = "pkg-config"
        return binaries

    @property
    def exe_wrapper_def(self):
        try:
            which("qemu-arm")
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exe_wrapper = 'qemu-arm'"

    @property
    def configure_options(self):
        yield "--host={}".format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, "bin")]

    def get_env(self):
        env = super().get_env()
        env["LD_LIBRARY_PATH"][0:0] = [
            pj(self.root_path, self.arch_full, "lib64"),
            pj(self.root_path, "lib")
        ]
        env["PKG_CONFIG_LIBDIR"] = pj(self.root_path, "lib", "pkgconfig")
        env["QEMU_LD_PREFIX"] = pj(self.root_path, self.arch_full, "libc")
        env["QEMU_SET_ENV"] = "LD_LIBRARY_PATH={}".format(
            get_separator().join(
                [pj(self.root_path, self.arch_full, "lib"), env["LD_LIBRARY_PATH"]]
            )
        )
        return env

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        env["CFLAGS"] = (
            " -fPIC -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "
            + env["CFLAGS"]
        )
        env["CXXFLAGS"] = (
            " -fPIC -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "
            + env["CXXFLAGS"]
        )

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile("cmake_cross_file.txt")
        self.buildEnv.meson_crossfile = self._gen_crossfile("meson_cross_file.txt")


class Armv6(ArmConfigInfo):
    build = "armv6"
    arch_full = "armv6-rpi-linux-gnueabihf"
    toolchain_names = ["armv6"]
    cpu_family = "arm"
    cpu = "armv6"


class Armv6Dyn(Armv6):
    name = "armv6_dyn"
    static = False


class Armv6Static(Armv6):
    name = "armv6_static"
    static = True


class Armv6Mixed(MixedMixin("armv6_static"), Armv6):
    name = "armv6_mixed"
    static = False


class Armv8(ArmConfigInfo):
    build = "armv8"
    arch_full = "armv8-rpi3-linux-gnueabihf"
    toolchain_names = ["armv8"]
    cpu_family = "arm"
    cpu = "armv8"


class Armv8Dyn(Armv8):
    name = "armv8_dyn"
    static = False


class Armv8Static(Armv8):
    name = "armv8_static"
    static = True


class Armv8Mixed(MixedMixin("armv8_static"), Armv8):
    name = "armv8_mixed"
    static = False


class Aarch64(ArmConfigInfo):
    build = "aarch64"
    arch_full = "aarch64-linux-gnu"
    toolchain_names = ["aarch64"]
    cpu_family = "aarch64"
    cpu = "aarch64"

    @property
    def root_path(self):
        return self.toolchain.build_path


class Aarch64Dyn(Aarch64):
    name = "aarch64_dyn"
    static = False


class Aarch64Static(Aarch64):
    name = "aarch64_static"
    static = True


class Aarch64Mixed(MixedMixin("aarch64_static"), Aarch64):
    name = "aarch64_mixed"
    static = False
