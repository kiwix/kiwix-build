from pathlib import Path
from .base import Dependency, ReleaseDownload, Builder
from kiwixbuild.utils import Remotefile, add_execution_right, run_command


class android_ndk(Dependency):
    dont_skip = True
    neutral = False
    name = "android-ndk"
    gccver = "4.9.x"
    api = "24"

    class Source(ReleaseDownload):
        archive = Remotefile(
            "android-ndk-r21e-linux-x86_64.zip",
            "ad7ce5467e18d40050dc51b8e7affc3e635c85bd8c59be62de32352328ed467e",
            "https://dl.google.com/android/repository/android-ndk-r21e-linux-x86_64.zip",
        )

        @property
        def source_dir(self):
            return self.target.full_name()

    class Builder(Builder):
        @property
        def install_path(self) -> Path:
            return self.buildEnv.toolchain_dir / self.target.full_name()

        @property
        def api(self):
            return self.target.api

        @property
        def config(self):
            return "android-" + self.api

        @property
        def arch(self):
            return self.buildEnv.configInfo.arch

        @property
        def arch_full(self):
            return self.buildEnv.configInfo.arch_full

        def _build_toolchain(self, context):
            context.try_skip(self.build_path)
            script = self.source_path / "build/tools/make_standalone_toolchain.py"
            add_execution_right(script)
            command = [
                script,
                f"--arch={self.arch}",
                f"--api={self.api}",
                f"--install-dir={self.install_path}",
                "--force",
            ]
            env = self.buildEnv.get_env(
                cross_comp_flags=False, cross_compilers=False, cross_path=False
            )
            run_command(command, self.build_path, context, env=env)

        def _fix_permission_right(self, context):
            context.try_skip(self.build_path)
            bin_dirs = [
                self.install_path / "bin",
                self.install_pat / self.arch_full / "bin",
                self.install_path
                / "libexec"
                / "gcc"
                / self.arch_full
                / self.target.gccver,
            ]
            for root, dirs, files in self.install_path.walk():
                if not root in bin_dirs:
                    continue

                for file_ in files:
                    file_path = root / file_
                    if file_path.is_symlink():
                        continue
                    add_execution_right(file_path)

        def build(self):
            self.command("build_toolchain", self._build_toolchain)
            self.command("fix_permission_right", self._fix_permission_right)
