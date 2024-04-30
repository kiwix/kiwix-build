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

    @property
    def arch_name(self):
        return sysconfig.get_platform()

    @property
    def config_wrapper(self):
        yield "C:\\Program Files\\Git\\bin\\bash.exe"

    @property
    def binaries(self):
        binaries = {
            "CC": "cl -nologo",
            "CXX": "cl -nologo",
            "AR": "lib",
        }
        return binaries

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        env["CXXFLAGS"] = "-EHsc -MD " + env["CXXFLAGS"]
