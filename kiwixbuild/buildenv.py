
import os, sys, shutil
import subprocess
import platform

from .platforms import PlatformInfo
from .toolchains import Toolchain
from .packages import PACKAGE_NAME_MAPPERS
from .utils import (
    pj,
    download_remote,
    Defaultdict)

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


class PlatformNeutralEnv:
    def __init__(self, options):
        self.options = options
        self.source_dir = pj(options.working_dir, "SOURCE")
        self.archive_dir = pj(options.working_dir, "ARCHIVE")
        self.toolchain_dir = pj(options.working_dir, "TOOLCHAINS")
        self.log_dir = pj(self.working_dir, 'LOGS')
        for d in (self.source_dir,
                  self.archive_dir,
                  self.toolchain_dir,
                  self.log_dir):
            os.makedirs(d, exist_ok=True)
        self.toolchains = {}
        self.detect_platform()
        self.ninja_command = self._detect_ninja()
        if not self.ninja_command:
            sys.exit("ERROR: ninja command not found")
        self.meson_command = self._detect_meson()
        if not self.meson_command:
            sys.exit("ERROR: meson command not fount")
        self.mesontest_command = "{} test".format(self.meson_command)

    def run_command(self, command, cwd, context, env=None, input=None):
        os.makedirs(cwd, exist_ok=True)
        if env is None:
            env = Defaultdict(str, os.environ)
        log = None
        try:
            if not self.options.verbose:
                log = open(context.log_file, 'w')
            print("run command '{}'".format(command), file=log)
            print("current directory is '{}'".format(cwd), file=log)
            print("env is :", file=log)
            for k, v in env.items():
                print("  {} : {!r}".format(k, v), file=log)

            kwargs = dict()
            if input:
                kwargs['stdin'] = subprocess.PIPE
            process = subprocess.Popen(command, shell=True, cwd=cwd, env=env, stdout=log or sys.stdout, stderr=subprocess.STDOUT, **kwargs)
            if input:
                process.communicate(input.encode())
            retcode = process.wait()
            if retcode:
                raise subprocess.CalledProcessError(retcode, command)
        finally:
            if log:
                log.close()

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
        download_remote(what, where, not self.options.no_cert_check)

    def _detect_ninja(self):
        for n in ['ninja', 'ninja-build']:
            try:
                retcode = subprocess.check_call([n, '--version'],
                                                stdout=subprocess.DEVNULL)
            except (FileNotFoundError, PermissionError):
                # Doesn't exist in PATH or isn't executable
                continue
            if retcode == 0:
                return n

    def add_toolchain(self, toolchain_name):
        if toolchain_name not in self.toolchains:
            ToolchainClass = Toolchain.all_toolchains[toolchain_name]
            self.toolchains[toolchain_name] = ToolchainClass(self)
        return self.toolchains[toolchain_name]

    def _detect_meson(self):
        for n in ['meson.py', 'meson']:
            try:
                retcode = subprocess.check_call([n, '--version'],
                                                stdout=subprocess.DEVNULL)
            except (FileNotFoundError, PermissionError):
                # Doesn't exist in PATH or isn't executable
                continue
            if retcode == 0:
                return n

    def __getattr__(self, name):
        return getattr(self.options, name)


class BuildEnv:
    def __init__(self, options, neutralEnv, targetsDict):
        build_dir = "BUILD_{}".format(options.target_platform)
        self.neutralEnv = neutralEnv
        self.build_dir = pj(options.working_dir, build_dir)
        self.install_dir = pj(self.build_dir, "INSTALL")
        for d in (self.build_dir,
                  self.install_dir):
            os.makedirs(d, exist_ok=True)

        self.setup_build(options.target_platform)
        self.setup_toolchains()
        self.options = options
        self.libprefix = options.libprefix or self._detect_libdir()
        self.targetsDict = targetsDict

    def clean_intermediate_directories(self):
        for subdir in os.listdir(self.build_dir):
            subpath = pj(self.build_dir, subdir)
            if subpath == self.install_dir:
                continue
            if os.path.isdir(subpath):
                shutil.rmtree(subpath)
            else:
                os.remove(subpath)

    def setup_build(self, target_platform):
        self.platform_info = PlatformInfo.all_platforms[target_platform]
        if self.distname not in self.platform_info.compatible_hosts:
            print(('ERROR: The target {} cannot be build on host {}.\n'
                   'Select another target platform, or change your host system.'
                  ).format(target_platform, self.distname))
            sys.exit(-1)
        self.cross_config = self.platform_info.get_cross_config()

    def setup_toolchains(self):
        toolchain_names = self.platform_info.toolchains
        self.toolchains = []
        for toolchain_name in toolchain_names:
            ToolchainClass = Toolchain.all_toolchains[toolchain_name]
            if ToolchainClass.neutral:
                self.toolchains.append(
                    self.neutralEnv.add_toolchain(toolchain_name)
                )
            else:
                self.toolchains.append(ToolchainClass(self))

    def finalize_setup(self):
        getattr(self, 'setup_{}'.format(self.platform_info.build))()

    def setup_native(self):
        self.cmake_crossfile = None
        self.meson_crossfile = None

    def _gen_crossfile(self, name):
        crossfile = pj(self.build_dir, name)
        template_file = pj(SCRIPT_DIR, 'templates', name)
        with open(template_file, 'r') as f:
            template = f.read()
        content = template.format(
            toolchain=self.toolchains[0],
            **self.cross_config
        )
        with open(crossfile, 'w') as outfile:
            outfile.write(content)
        return crossfile

    def setup_win32(self):
        self.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
        self.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

    def setup_android(self):
        self.cmake_crossfile = self._gen_crossfile('cmake_android_cross_file.txt')
        self.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

    def setup_armhf(self):
        self.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
        self.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

    def setup_iOS(self):
        self.cmake_crossfile = self._gen_crossfile('cmake_ios_cross_file.txt')
        self.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

    def setup_i586(self):
        self.cmake_crossfile = self._gen_crossfile('cmake_i586_cross_file.txt')
        self.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')

    def __getattr__(self, name):
        return getattr(self.neutralEnv, name)

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

    @property
    def configure_option(self):
        configure_options = [tlc.configure_option for tlc in self.toolchains]
        return " ".join(configure_options)

    @property
    def cmake_option(self):
        cmake_options = [tlc.cmake_option for tlc in self.toolchains]
        return " ".join(cmake_options)

    def _set_env(self, env, cross_compile_env, cross_compile_compiler, cross_compile_path):
        if env is None:
            env = Defaultdict(str, os.environ)

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

        env['CPPFLAGS'] = " ".join(['-I'+pj(self.install_dir, 'include'), env['CPPFLAGS']])
        env['LDFLAGS'] = " ".join(['-L'+pj(self.install_dir, 'lib'),
                                   '-L'+pj(self.install_dir, self.libprefix),
                                   env['LDFLAGS']])

        if cross_compile_env:
            for k, v in self.cross_config.get('env', {}).items():
                if k.startswith('_format_'):
                    v = v.format(**self.cross_config)
                    k = k[8:]
                env[k] = v
            for toolchain in self.toolchains:
                toolchain.set_env(env)
            self.platform_info.set_env(env)
        if cross_compile_compiler:
            for toolchain in self.toolchains:
                toolchain.set_compiler(env)
        if cross_compile_path:
            bin_dirs = []
            for tlc in self.toolchains:
                bin_dirs += tlc.get_bin_dir()
            bin_dirs += self.platform_info.get_bind_dir()
            env['PATH'] = ':'.join(bin_dirs + [env['PATH']])
        return env

    def run_command(self, command, cwd, context, env=None, input=None, cross_env_only=False):
        os.makedirs(cwd, exist_ok=True)
        cross_compile_env = True
        cross_compile_compiler = True
        cross_compile_path = True
        if context.force_native_build:
            cross_compile_env = False
            cross_compile_compiler = False
            cross_compile_path = False
        if cross_env_only:
            cross_compile_compiler = False
        env = self._set_env(env, cross_compile_env, cross_compile_compiler, cross_compile_path)
        log = None
        try:
            if not self.options.verbose:
                log = open(context.log_file, 'w')
            print("run command '{}'".format(command), file=log)
            print("current directory is '{}'".format(cwd), file=log)
            print("env is :", file=log)
            for k, v in env.items():
                print("  {} : {!r}".format(k, v), file=log)

            kwargs = dict()
            if input:
                kwargs['stdin'] = subprocess.PIPE
            process = subprocess.Popen(command, shell=True, cwd=cwd, env=env, stdout=log or sys.stdout, stderr=subprocess.STDOUT, **kwargs)
            if input:
                process.communicate(input.encode())
            retcode = process.wait()
            if retcode:
                raise subprocess.CalledProcessError(retcode, command)
        finally:
            if log:
                log.close()

    def install_packages(self):
        autoskip_file = pj(self.build_dir, ".install_packages_ok")
        if self.distname in ('fedora', 'redhat', 'centos'):
            package_installer = 'sudo dnf install {}'
            package_checker = 'rpm -q --quiet {}'
        elif self.distname in ('debian', 'Ubuntu'):
            package_installer = 'sudo apt-get install {}'
            package_checker = 'LANG=C dpkg -s {} 2>&1 | grep Status | grep "ok installed" 1>/dev/null 2>&1'
        elif self.distname == 'Darwin':
            package_installer = 'brew install {}'
            package_checker = 'brew list -1 | grep -q {}'
        mapper_name = "{host}_{target}".format(
            host=self.distname,
            target=self.platform_info)
        try:
            package_name_mapper = PACKAGE_NAME_MAPPERS[mapper_name]
        except KeyError:
            print("SKIP : We don't know which packages we must install to compile"
                  " a {target} {build_type} version on a {host} host.".format(
                      target=self.platform_info,
                      host=self.distname))
            return

        packages_list = package_name_mapper.get('COMMON', [])
        for dep in self.targetsDict.values():
            packages = package_name_mapper.get(dep.name)
            if packages:
                packages_list += packages
                dep.skip = True
        for dep in self.targetsDict.values():
            packages = getattr(dep, 'extra_packages', [])
            for package in packages:
                packages_list += package_name_mapper.get(package, [])
        if not self.options.force_install_packages and os.path.exists(autoskip_file):
            print("SKIP")
            return

        packages_to_install = []
        for package in packages_list:
            print(" - {} : ".format(package), end="")
            command = package_checker.format(package)
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError:
                print("NEEDED")
                packages_to_install.append(package)
            else:
                print("SKIP")

        if packages_to_install:
            command = package_installer.format(" ".join(packages_to_install))
            print(command)
            subprocess.check_call(command, shell=True)
        else:
            print("SKIP, No package to install.")

        with open(autoskip_file, 'w'):
            pass
