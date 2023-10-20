
import os, sys, shutil
import subprocess
import platform
import distro

from .utils import pj, download_remote, Defaultdict
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
            sys.exit("ERROR: ninja command not found.")
        self.meson_command = self._detect_meson()
        if not self.meson_command:
            sys.exit("ERROR: meson command not found.")
        self.qmake_command = self._detect_qmake()
        if not self.qmake_command:
            print("WARNING: qmake command not found.", file=sys.stderr)
        self.mesontest_command = "{} test".format(self.meson_command)

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
            self.distname = distro.id()
            if self.distname == 'ubuntu':
                self.distname = 'debian'

    def download(self, what, where=None):
        where = where or self.archive_dir
        download_remote(what, where)

    def _detect_binary(self, *bin_variants):
        for n in bin_variants:
            try:
                retcode = subprocess.check_call([n, '--version'],
                                                stdout=subprocess.DEVNULL)
            except (FileNotFoundError, PermissionError):
                # Doesn't exist in PATH or isn't executable
                continue
            if retcode == 0:
                return n


    def _detect_ninja(self):
        return self._detect_binary('ninja', 'ninja-build')

    def _detect_meson(self):
        return self._detect_binary('meson.py', 'meson')

    def _detect_qmake(self):
        return self._detect_binary('qmake-qt5', 'qmake')


class BuildEnv:
    def __init__(self, platformInfo):
        build_dir = "BUILD_{}".format(platformInfo.name)
        self.platformInfo = platformInfo
        self.base_build_dir = pj(option('working_dir'), option('build_dir'))
        self.build_dir = pj(self.base_build_dir, build_dir)
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
        if self.platformInfo.libdir is not None:
            return self.platformInfo.libdir
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

    def get_env(self, *, cross_comp_flags, cross_compilers, cross_path):
        env = self.platformInfo.get_env()
        pkgconfig_path = pj(self.install_dir, self.libprefix, 'pkgconfig')
        env['PKG_CONFIG_PATH'] = ':'.join([env['PKG_CONFIG_PATH'], pkgconfig_path])

        env['PATH'] = ':'.join([pj(self.install_dir, 'bin'), env['PATH']])

        env['QMAKE_CXXFLAGS'] = " ".join(['-I'+pj(self.install_dir, 'include'), env['QMAKE_CXXFLAGS']])
        env['CPPFLAGS'] = " ".join(['-I'+pj(self.install_dir, 'include'), env['CPPFLAGS']])
        env['QMAKE_LFLAGS'] = " ".join(['-L'+pj(self.install_dir, 'lib'),
                                   '-L'+pj(self.install_dir, self.libprefix),
                                   env['QMAKE_LFLAGS']])
        env['LDFLAGS'] = " ".join(['-L'+pj(self.install_dir, 'lib'),
                                   '-L'+pj(self.install_dir, self.libprefix),
                                   env['LDFLAGS']])

        if cross_comp_flags:
            env['LD_LIBRARY_PATH'] = ':'.join([env['LD_LIBRARY_PATH'],
                pj(self.install_dir, 'lib'),
                pj(self.install_dir, self.libprefix)
            ])
            self.platformInfo.set_comp_flags(env)
        if cross_compilers:
            self.platformInfo.set_compiler(env)
        if cross_path:
            env['PATH'] = ':'.join(self.platformInfo.get_bin_dir() + [env['PATH']])
        return env


    @property
    def configure_wrapper(self):
        wrapper = getattr(self.platformInfo, "configure_wrapper", "")
        if wrapper:
            return "{} ".format(wrapper)
        else:
            return ""

    @property
    def make_wrapper(self):
        wrapper = getattr(self.platformInfo, "make_wrapper", "")
        if wrapper:
            return "{} ".format(wrapper)
        else:
            return ""

