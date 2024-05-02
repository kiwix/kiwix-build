import os, sys, shutil
import subprocess
import platform
import distro
from pathlib import Path

from .utils import download_remote, escape_path, win_to_posix_path
from ._global import neutralEnv, option


class NeutralEnv:
    def __init__(self, dummy_run):
        self.working_dir: Path = option("working_dir")
        self.source_dir: Path = self.working_dir / "SOURCE"
        self.archive_dir: Path = self.working_dir / "ARCHIVE"
        self.toolchain_dir: Path = self.working_dir / "TOOLCHAINS"
        self.log_dir: Path = self.working_dir / "LOGS"
        for d in (self.source_dir, self.archive_dir, self.toolchain_dir, self.log_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.detect_platform()
        if dummy_run:
            # If this is for a dummy run, we will not run anything.
            # To check for command (and so, don't enforce their presence)
            return
        self.ninja_command = self._detect_command(
            "ninja", default=[["ninja"], ["ninja-build"]]
        )
        self.meson_command = self._detect_command(
            "meson", default=[["meson.py"], ["meson"]]
        )
        self.mesontest_command = [*self.meson_command, "test"]
        self.patch_command = self._detect_command("patch")
        self.git_command = self._detect_command("git")
        self.make_command = self._detect_command("make")
        self.cmake_command = self._detect_command("cmake")
        self.qmake_command = self._detect_command("qmake", required=False)

    def detect_platform(self):
        _platform = platform.system()
        self.distname = _platform
        if _platform == "Linux":
            self.distname = distro.id()
            if self.distname == "ubuntu":
                self.distname = "debian"

    def download(self, what, where=None):
        where = where or self.archive_dir
        download_remote(what, where)

    def _detect_command(self, name, default=None, options=["--version"], required=True):
        if default is None:
            default = [[name]]
        env_key = f"KBUILD_{name.upper()}_COMMAND"
        if env_key in os.environ:
            default = [os.environ[env_key].split()] + default
        for command in default:
            try:
                retcode = subprocess.check_call(
                    command + options, stdout=subprocess.DEVNULL
                )
            except (FileNotFoundError, PermissionError, OSError):
                # Doesn't exist in PATH or isn't executable
                continue
            if retcode == 0:
                return command
        else:
            if required:
                sys.exit(f"ERROR: {name} command not found")
            else:
                print(f"WARNING: {name} command not found", file=sys.stderr)
                return [f"{name.upper()}_NOT_FOUND"]


class BuildEnv:
    def __init__(self, configInfo):
        self.configInfo = configInfo
        self.base_build_dir: Path = option("working_dir") / option("build_dir")
        build_dir = (
            configInfo.arch_name if option("use_target_arch_name") else configInfo.name
        )
        build_dir = f"BUILD_{build_dir}"
        self.build_dir: Path = self.base_build_dir / build_dir
        self.install_dir: Path = self.build_dir / "INSTALL"
        self.toolchain_dir: Path = self.build_dir / "TOOLCHAINS"
        self.log_dir: Path = self.build_dir / "LOGS"
        for d in (self.build_dir, self.install_dir, self.toolchain_dir, self.log_dir):
            d.mkdir(parents=True, exist_ok=True)

        self.libprefix = option("libprefix") or self._detect_libdir()

    def clean_intermediate_directories(self):
        for subpath in self.build_dir.iterdir():
            if subpath == self.install_dir:
                continue
            if subpath.isdir():
                shutil.rmtree(subpath)
            else:
                subpath.unlink()

    def _is_debianlike(self):
        return os.path.isfile("/etc/debian_version")

    def _detect_libdir(self):
        if self.configInfo.libdir is not None:
            return self.configInfo.libdir
        if self._is_debianlike():
            try:
                pc = subprocess.Popen(
                    ["dpkg-architecture", "-qDEB_HOST_MULTIARCH"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                (stdo, _) = pc.communicate()
                if pc.returncode == 0:
                    archpath = stdo.decode().strip()
                    return "lib/" + archpath
            except Exception:
                pass
        if os.path.isdir("/usr/lib64") and not os.path.islink("/usr/lib64"):
            return "lib64"
        return "lib"

    def get_env(self, *, cross_comp_flags, cross_compilers, cross_path):
        env = self.configInfo.get_env()
        if self.configInfo.force_posix_path:
            tr_path = win_to_posix_path
        else:
            tr_path = lambda v: v
        pkgconfig_path = self.install_dir / self.libprefix / "pkgconfig"
        env["PKG_CONFIG_PATH"].append(tr_path(pkgconfig_path))

        env["PATH"].insert(0, tr_path(self.install_dir / "bin"))

        env["LD_LIBRARY_PATH"].extend(
            [
                tr_path(self.install_dir / "lib"),
                tr_path(self.install_dir / self.libprefix),
            ]
        )

        env["QMAKE_CXXFLAGS"] = " ".join(
            [
                escape_path(f"-I{tr_path(self.install_dir / 'include')}"),
                env["QMAKE_CXXFLAGS"],
            ]
        )
        env["CPPFLAGS"] = " ".join(
            [escape_path(f"-I{tr_path(self.install_dir / 'include')}"), env["CPPFLAGS"]]
        )
        env["QMAKE_LFLAGS"] = " ".join(
            [
                escape_path(f"-L{tr_path(self.install_dir / 'lib')}"),
                escape_path(f"-L{tr_path(self.install_dir / self.libprefix)}"),
                env["QMAKE_LFLAGS"],
            ]
        )
        env["LDFLAGS"] = " ".join(
            [
                escape_path(f"-L{tr_path(self.install_dir / 'lib')}"),
                escape_path(f"-L{tr_path(self.install_dir / self.libprefix)}"),
                env["LDFLAGS"],
            ]
        )

        if cross_comp_flags:
            self.configInfo.set_comp_flags(env)
        if cross_compilers:
            self.configInfo.set_compiler(env)
        if cross_path:
            env["PATH"][0:0] = self.configInfo.get_bin_dir()
        return env

    @property
    def configure_wrapper(self):
        try:
            yield from self.configInfo.configure_wrapper
        except AttributeError:
            pass

    @property
    def make_wrapper(self):
        try:
            yield from self.configInfo.make_wrapper
        except AttributeError:
            pass
