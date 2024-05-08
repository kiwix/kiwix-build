from .base import ConfigInfo
import sysconfig

from kiwixbuild._global import get_target_step


class WinBashConfigInfo(ConfigInfo):
    """This config is kind of internal config to compile xapian using git bash."""

    build = "winbash"
    name = "win_bash"
    compatible_hosts = ["Windows"]
    exe_wrapper_def = ""
    static = True
    force_posix_path = True

    @property
    def arch_name(self):
        return sysconfig.get_platform()

    @property
    def configure_wrapper(self):
        # yield "C:\\msys64\\usr\\bin\\bash.exe"
        yield "C:\\msys64\\usr\\bin\\bash.exe"

    @property
    def make_wrapper(self):
        return []
        # yield "C:\\msys64\\usr\\bin\\bash.exe"
        yield "C:\\msys64\\usr\\bin\\bash.exe"
        yield "-c"

    @property
    def binaries(self):
        binaries = {
            "CC": "cl -nologo",
            "CXX": "cl -nologo",
            "AR": "lib",
        }
        return binaries

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        env["CXXFLAGS"] = "-EHsc -MD " + env["CXXFLAGS"]

    def get_env(self):
        env = super().get_env()
        #        PATH_ENV = env["PATH"]
        #        PATH_ENV = filter(
        #            lambda p: p
        #            not in ["C:\\Program Files\\Git\\bin", "C:\\Program Files\\Git\\usr\\bin"],
        #            PATH_ENV,
        #        )
        #        env["PATH"][:] = list(PATH_ENV)
        #        env["PATH"] += ["C:\\msys64\\usr\\bin"]
        env["SHELL"] = "C:\\msys64\\usr\\bin\\bash.exe"
        env["CONFIG_SHELL"] = "C:\\msys64\\usr\\bin\\bash.exe"
        return env
