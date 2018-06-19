
import os, sys, shutil
import subprocess
import platform

from .utils import pj, download_remote, DefaultEnv, escape_path
from ._global import neutralEnv, option


class PlatformNeutralEnv:
    def __init__(self):
        self.working_dir = option('working_dir')
        self.source_dir = pj(self.working_dir, "SOURCE")
        self.archive_dir = pj(self.working_dir, "ARCHIVE")
        self.toolchain_dir = pj(self.working_dir, "TOOLCHAINS")
        self.log_dir = pj(self.working_dir, 'LOGS')
        for d in (self.source_dir,
                  self.archive_dir,
                  self.toolchain_dir,
                  self.log_dir):
            os.makedirs(d, exist_ok=True)
        self.detect_platform()
        self.ninja_command = self._detect_ninja()
        if not self.ninja_command:
            sys.exit("ERROR: ninja command not found")
        self.meson_command = self._detect_meson()
        if not self.meson_command:
            sys.exit("ERROR: meson command not fount")
        self.mesontest_command = [*self.meson_command, "test"]

    def detect_platform(self):
        _platform = platform.system()
        self.distname = _platform
        if _platform == 'Windows':
            print('ERROR: kiwix-build is not intented to run on Windows platform.\n'
                  'It should probably not work, but well, you still can have a try.')
            cont = input('Do you want to continue ? [y/N]')
            if cont.lower() != 'y':
                sys.exit(0)
        if _platform == 'Linux':
            self.distname, _, _ = platform.linux_distribution()
            self.distname = self.distname.lower()
            if self.distname == 'ubuntu':
                self.distname = 'debian'

    def download(self, what, where=None):
        where = where or self.archive_dir
        download_remote(what, where)

    def _detect_ninja(self):
        for n in ['ninja', 'ninja-build']:
            try:
                retcode = subprocess.check_call([n, '--version'],
                                                stdout=subprocess.DEVNULL)
            except (FileNotFoundError, PermissionError):
                # Doesn't exist in PATH or isn't executable
                continue
            if retcode == 0:
                return [n]

    def _detect_meson(self):
        for n in ['meson.py', 'meson']:
            try:
                retcode = subprocess.check_call([n, '--version'],
                                                stdout=subprocess.DEVNULL)
            except (FileNotFoundError, PermissionError):
                # Doesn't exist in PATH or isn't executable
                continue
            if retcode == 0:
                return [n]


class BuildEnv:
    def __init__(self, platformInfo):
        build_dir = "BUILD_{}".format(platformInfo.name)
        self.platformInfo = platformInfo
        self.build_dir = pj(option('working_dir'), build_dir)
        self.install_dir = pj(self.build_dir, "INSTALL")
        self.toolchain_dir = pj(self.build_dir, "TOOLCHAINS")
        self.log_dir = pj(self.build_dir, 'LOGS')
        for d in (self.build_dir,
                  self.install_dir,
                  self.toolchain_dir,
                  self.log_dir):
            os.makedirs(d, exist_ok=True)

        self.libprefix = option('libprefix') or self._detect_libdir()

    def clean_intermediate_directories(self):
        for subdir in os.listdir(self.build_dir):
            subpath = pj(self.build_dir, subdir)
            if subpath == self.install_dir:
                continue
            if os.path.isdir(subpath):
                shutil.rmtree(subpath)
            else:
                os.remove(subpath)

    def _is_debianlike(self):
        return os.path.isfile('/etc/debian_version')

    def _detect_libdir(self):
        if self._is_debianlike():
            try:
                pc = subprocess.Popen(['dpkg-architecture', '-qDEB_HOST_MULTIARCH'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL)
                (stdo, _) = pc.communicate()
                if pc.returncode == 0:
                    archpath = stdo.decode().strip()
                    return 'lib/' + archpath
            except Exception:
                pass
        if os.path.isdir('/usr/lib64') and not os.path.islink('/usr/lib64'):
            return 'lib64'
        return 'lib'

    def _set_env(self, env, cross_compile_env, cross_compile_compiler, cross_compile_path):
        if env is None:
            env = DefaultEnv()

        pkgconfig_path = pj(self.install_dir, self.libprefix, 'pkgconfig')
        env['PKG_CONFIG_PATH'] = ':'.join([env['PKG_CONFIG_PATH'], pkgconfig_path])

        # Add ccache path
        for p in ('/usr/lib/ccache', '/usr/lib64/ccache'):
            if os.path.isdir(p):
                ccache_path = [p]
                break
        else:
            ccache_path = []
        env['PATH'] = ':'.join([pj(self.install_dir, 'bin')] +
                               ccache_path +
                               [env['PATH']])

        env['LD_LIBRARY_PATH'] = ':'.join([env['LD_LIBRARY_PATH'],
                                          pj(self.install_dir, 'lib'),
                                          pj(self.install_dir, self.libprefix)
                                          ])

        env['QMAKE_CXXFLAGS'] = " ".join([
            escape_path('-I'+pj(self.install_dir, 'include')),
            env['QMAKE_CXXFLAGS']
        ])
        env['CPPFLAGS'] = " ".join([
            escape_path('-I'+pj(self.install_dir, 'include')),
            env['CPPFLAGS']
        ])
        env['QMAKE_LFLAGS'] = " ".join([
            escape_path('-L'+pj(self.install_dir, 'lib')),
            escape_path('-L'+pj(self.install_dir, self.libprefix)),
            env['QMAKE_LFLAGS']
        ])
        env['LDFLAGS'] = " ".join([
            escape_path('-L'+pj(self.install_dir, 'lib')),
            escape_path('-L'+pj(self.install_dir, self.libprefix)),
            env['LDFLAGS']
        ])

        if cross_compile_env:
            for k, v in self.cross_config.get('env', {}).items():
                if k.startswith('_format_'):
                    v = v.format(**self.cross_config)
                    k = k[8:]
                env[k] = v
            self.platformInfo.set_env(env)
        if cross_compile_compiler:
            self.platformInfo.set_compiler(env)
        if cross_compile_path:
            bin_dirs = self.platformInfo.get_bind_dir()
            env['PATH'] = ':'.join(bin_dirs + [env['PATH']])
        return env
