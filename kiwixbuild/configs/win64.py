import subprocess

from pathlib import Path
from .base import ConfigInfo
from kiwixbuild.utils import which
from kiwixbuild._global import neutralEnv


class Win64ConfigInfo(ConfigInfo):
    extra_libs = [
        "-lmingw32",
        "-lwinmm",
        "-lws2_32",
        "-lshlwapi",
        "-lrpcrt4",
        "-lmsvcr100",
        "-liphlpapi",
        "-lshell32",
        "-lkernel32",
    ]
    build = "win64"
    compatible_hosts = ["fedora", "debian"]
    arch_full = "x86_64-w64-mingw32"

    def get_cross_config(self):
        return {
            "exe_wrapper_def": self.exe_wrapper_def,
            "binaries": self.binaries,
            "root_path": self.root_path,
            "extra_libs": self.extra_libs,
            "extra_cflags": ["-DWIN32"],
            "host_machine": {
                "system": "Windows",
                "lsystem": "windows",
                "cpu_family": "x86_64",
                "cpu": "x86_64",
                "endian": "little",
                "abi": "",
            },
        }

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile("cmake_cross_file.txt")
        self.buildEnv.meson_crossfile = self._gen_crossfile("meson_cross_file.txt")

    @property
    def root_path(self) -> Path:
        root_paths = {
            "fedora": "/usr/x86_64-w64-mingw32/sys-root/mingw",
            "debian": "/usr/x86_64-w64-mingw32",
        }
        return Path(root_paths[neutralEnv("distname")])

    @property
    def binaries(self):
        return {
            k: which(f"{self.arch_full}-{v}")
            for k, v in (
                ("CC", "gcc"),
                ("CXX", "g++"),
                ("AR", "ar"),
                ("STRIP", "strip"),
                ("WINDRES", "windres"),
                ("RANLIB", "ranlib"),
                ("PKGCONFIG", "pkg-config"),
            )
        }

    @property
    def exe_wrapper_def(self):
        try:
            which("wine")
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exe_wrapper = 'wine'"

    @property
    def configure_options(self):
        return [f"--host={self.arch_full}"]

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v

    def get_bin_dir(self):
        return [self.root_path / "bin"]

    def get_env(self):
        env = super().get_env()
        env["PKG_CONFIG_LIBDIR"] = self.root_path / "lib" / "pkgconfig"
        env["LIBS"] = " ".join(self.extra_libs) + " " + env["LIBS"]
        return env


class Win64Dyn(Win64ConfigInfo):
    name = "win64_dyn"
    static = False


class Win64Static(Win64ConfigInfo):
    name = "win64_static"
    static = True
