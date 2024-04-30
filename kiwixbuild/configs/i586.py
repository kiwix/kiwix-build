import os

from .base import ConfigInfo
from kiwixbuild.utils import which


class I586ConfigInfo(ConfigInfo):
    build = "i586"
    arch_full = "i586-linux-gnu"
    compatible_hosts = ["fedora", "debian"]

    def get_cross_config(self):
        return {
            "binaries": self.binaries,
            "exe_wrapper_def": "",
            "extra_libs": ["-m32", "-march=i586", "-mno-sse"],
            "extra_cflags": [
                "-m32",
                "-march=i586",
                "-mno-sse",
                *(
                    "-I{}".format(include_dir)
                    for include_dir in self.get_include_dirs()
                ),
            ],
            "host_machine": {
                "system": "linux",
                "lsystem": "linux",
                "cpu_family": "x86",
                "cpu": "i586",
                "endian": "little",
                "abi": "",
            },
        }

    @property
    def configure_options(self):
        yield f"--host={self.arch_full}"

    @property
    def binaries(self):
        return {
            k: which(v)
            for k, v in (
                ("CC", os.environ.get("CC", "gcc")),
                ("CXX", os.environ.get("CXX", "g++")),
                ("AR", "ar"),
                ("STRIP", "strip"),
                ("RANLIB", "ranlib"),
                ("LD", "ld"),
                ("PKGCONFIG", "pkg-config"),
            )
        }

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        env["CFLAGS"] = "-m32 -march=i586 -mno-sse " + env["CFLAGS"]
        env["CXXFLAGS"] = "-m32 -march=i586 -mno-sse " + env["CXXFLAGS"]
        env["LDFLAGS"] = "-m32 -march=i586 -mno-sse " + env["LDFLAGS"]

    def get_bin_dir(self):
        return []

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile(
            "cmake_i586_cross_file.txt", "cmake_cross_file.txt"
        )
        self.buildEnv.meson_crossfile = self._gen_crossfile("meson_cross_file.txt")


class I586Dyn(I586ConfigInfo):
    name = "i586_dyn"
    static = False


class I586Static(I586ConfigInfo):
    name = "i586_static"
    static = True
