#!/usr/bin/env python3

import os, sys, shutil
import argparse
import ssl
import urllib.request
import subprocess
import platform
from collections import OrderedDict

from dependencies import Dependency
from dependency_utils import ReleaseDownload, Builder, GitClone
from utils import (
    pj,
    remove_duplicates,
    add_execution_right,
    get_sha256,
    print_progress,
    setup_print_progress,
    download_remote,
    StopBuild,
    SkipCommand,
    Defaultdict,
    Remotefile,
    Context)

REMOTE_PREFIX = 'http://download.kiwix.org/dev/'

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


_fedora_common = ['automake', 'cmake', 'git', 'subversion', 'ccache', 'pkgconfig', 'gcc-c++', 'gettext-devel']
_debian_common = ['automake', 'cmake', 'git', 'subversion', 'ccache', 'pkg-config', 'gcc', 'autopoint']
PACKAGE_NAME_MAPPERS = {
    'fedora_native_dyn': {
        'COMMON': _fedora_common,
        'uuid': ['libuuid-devel'],
        'xapian-core': None, # Not the right version on fedora 25
        'ctpp2': None,
        'pugixml': None, # ['pugixml-devel'] but package doesn't provide pkg-config file
        'libmicrohttpd': ['libmicrohttpd-devel'],
        'zlib': ['zlib-devel'],
        'lzma': ['xz-devel'],
        'icu4c': None,
        'zimlib': None,
        'file' : ['file-devel'],
        'gumbo' : ['gumbo-parser-devel'],
    },
    'fedora_native_static': {
        'COMMON': _fedora_common + ['glibc-static', 'libstdc++-static'],
        'zlib': ['zlib-devel', 'zlib-static'],
        'lzma': ['xz-devel', 'xz-static']
        # Either there is no packages, or no static or too old
    },
    'fedora_win32_dyn': {
        'COMMON': _fedora_common + ['mingw32-gcc-c++', 'mingw32-bzip2', 'mingw32-win-iconv', 'mingw32-winpthreads', 'wine'],
        'zlib': ['mingw32-zlib'],
        'lzma': ['mingw32-xz-libs'],
        'libmicrohttpd': ['mingw32-libmicrohttpd'],
    },
    'fedora_win32_static': {
        'COMMON': _fedora_common + ['mingw32-gcc-c++', 'mingw32-bzip2-static', 'mingw32-win-iconv-static', 'mingw32-winpthreads-static', 'wine'],
        'zlib': ['mingw32-zlib-static'],
        'lzma': ['mingw32-xz-libs-static'],
        'libmicrohttpd': None, # ['mingw32-libmicrohttpd-static'] packaging dependecy seems buggy, and some static lib are name libfoo.dll.a and
                               # gcc cannot found them.
    },
    'fedora_armhf_static': {
        'COMMON': _fedora_common
    },
    'fedora_armhf_dyn': {
        'COMMON': _fedora_common
    },
    'fedora_android': {
        'COMMON': _fedora_common + ['java-1.8.0-openjdk-devel']
    },
    'debian_native_dyn': {
        'COMMON': _debian_common + ['libbz2-dev', 'libmagic-dev'],
        'zlib': ['zlib1g-dev'],
        'uuid': ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
        'ctpp2c': ['ctpp2-utils'],
        'libmicrohttpd': ['libmicrohttpd-dev', 'ccache']
    },
    'debian_native_static': {
        'COMMON': _debian_common + ['libbz2-dev', 'libmagic-dev'],
        'zlib': ['zlib1g-dev'],
        'uuid': ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
        'ctpp2c': ['ctpp2-utils'],
    },
    'debian_win32_dyn': {
        'COMMON': _debian_common + ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools'],
        'ctpp2c': ['ctpp2-utils'],
    },
    'debian_win32_static': {
        'COMMON': _debian_common + ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools'],
        'ctpp2c': ['ctpp2-utils'],
    },
    'debian_armhf_static': {
        'COMMON': _debian_common,
        'ctpp2c': ['ctpp2-utils'],
    },
    'debian_armhf_dyn': {
        'COMMON': _debian_common,
        'ctpp2c': ['ctpp2-utils'],
    },
    'debian_android': {
        'COMMON': _debian_common + ['default-jdk'],
        'ctpp2c': ['ctpp2-utils'],
    },
    'Darwin_native_dyn': {
        'COMMON': ['autoconf', 'automake', 'libtool', 'cmake', 'pkg-config'],
    },
    'Darwin_iOS': {
        'COMMON': ['autoconf', 'automake', 'libtool', 'cmake', 'pkg-config'],
    },
}


def which(name):
    command = "which {}".format(name)
    output = subprocess.check_output(command, shell=True)
    return output[:-1].decode()

def xrun_find(name):
    command = "xcrun -find {}".format(name)
    output = subprocess.check_output(command, shell=True)
    return output[:-1].decode()

class TargetInfo:
    def __init__(self, build, static, toolchains, hosts=None):
        self.build = build
        self.static = static
        self.toolchains = toolchains
        self.compatible_hosts = hosts

    def __str__(self):
        return "{}_{}".format(self.build, 'static' if self.static else 'dyn')

    def get_cross_config(self, host):
        if self.build == 'native':
            return {}
        elif self.build == 'win32':
            root_paths = {
                'fedora': '/usr/i686-w64-mingw32/sys-root/mingw',
                'debian': '/usr/i686-w64-mingw32'
            }
            return {
                'root_path': root_paths[host],
                'extra_libs': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4', '-lmsvcr90'],
                'extra_cflags': ['-DWIN32'],
                'host_machine': {
                    'system': 'Windows',
                    'lsystem': 'windows',
                    'cpu_family': 'x86',
                    'cpu': 'i686',
                    'endian': 'little',
                    'abi': ''
                }
            }
        elif self.build == 'armhf':
            return {
                'extra_libs': [],
                'extra_cflags': [],
                'host_machine': {
                    'system': 'linux',
                    'lsystem': 'linux',
                    'cpu_family': 'arm',
                    'cpu': 'armhf',
                    'endian': 'little',
                    'abi': ''
                }
            }

class AndroidTargetInfo(TargetInfo):
    __arch_infos = {
        'arm' : ('arm-linux-androideabi', 'arm', 'armeabi'),
        'arm64': ('aarch64-linux-android', 'aarch64', 'arm64-v8a'),
        'mips': ('mipsel-linux-android', 'mipsel', 'mips'),
        'mips64': ('mips64el-linux-android', 'mips64el', 'mips64'),
        'x86': ('i686-linux-android', 'i686', 'x86'),
        'x86_64': ('x86_64-linux-android', 'x86_64', 'x86_64'),
    }

    def __init__(self, arch):
        super().__init__('android', True, ['android_ndk', 'android_sdk'],
                         hosts=['fedora', 'debian'])
        self.arch = arch
        self.arch_full, self.cpu, self.abi = self.__arch_infos[arch]

    def __str__(self):
        return "android"

    def get_cross_config(self, host):
        return {
            'extra_libs': [],
            'extra_cflags': [],
            'host_machine': {
                'system': 'Android',
                'lsystem': 'android',
                'cpu_family': self.arch,
                'cpu': self.cpu,
                'endian': 'little',
                'abi': self.abi
            },
        }

class iOSTargetInfo(TargetInfo):
    __arch_infos = {
        'armv7s': ('arm-apple-darwin', 'armv7s', 'iphoneos'),
        'arm64': ('arm-apple-darwin', 'arm64', 'iphoneos'),
        'i386': ('', 'i386', 'iphonesimulator'),
        'x86_64': ('', 'x86_64', 'iphonesimulator'),
    }

    def __init__(self, arch):
        super().__init__('iOS', True, ['iOS_sdk'],
                         hosts=['Darwin'])
        self.arch = arch
        self.arch_full, self.cpu, self.sdk_name = self.__arch_infos[arch]
        command = "xcodebuild -version -sdk {} | grep -E '^Path' | sed 's/Path: //'".format(self.sdk_name)
        self.root_path = subprocess.check_output(command, shell=True)[:-1].decode()

    def __str__(self):
        return "iOS"

    def get_cross_config(self, host):
        return {
            'extra_libs': ['-fembed-bitcode', '-isysroot', self.root_path, '-arch', self.arch, '-miphoneos-version-min=9.0', '-stdlib=libc++'],
            'extra_cflags': ['-fembed-bitcode', '-isysroot', self.root_path, '-arch', self.arch, '-miphoneos-version-min=9.0', '-stdlib=libc++'],
            'host_machine': {
                'system': 'Darwin',
                'lsystem': 'darwin',
                'cpu_family': self.arch,
                'cpu': self.cpu,
                'endian': '',
                'abi': ''
            },
        }


class BuildEnv:
    target_platforms = {
        'native_dyn': TargetInfo('native', False, [],
                                 hosts=['fedora', 'debian', 'Darwin']),
        'native_static': TargetInfo('native', True, [],
                                 hosts=['fedora', 'debian']),
        'win32_dyn': TargetInfo('win32', False, ['mingw32_toolchain'],
                                 hosts=['fedora', 'debian']),
        'win32_static': TargetInfo('win32', True, ['mingw32_toolchain'],
                                 hosts=['fedora', 'debian']),
        'armhf_dyn': TargetInfo('armhf', False, ['armhf_toolchain'],
                                 hosts=['fedora', 'debian']),
        'armhf_static': TargetInfo('armhf', True, ['armhf_toolchain'],
                                 hosts=['fedora', 'debian']),
        'android_arm': AndroidTargetInfo('arm'),
        'android_arm64': AndroidTargetInfo('arm64'),
        'android_mips': AndroidTargetInfo('mips'),
        'android_mips64': AndroidTargetInfo('mips64'),
        'android_x86': AndroidTargetInfo('x86'),
        'android_x86_64': AndroidTargetInfo('x86_64'),
        'iOS_armv7s': iOSTargetInfo('armv7s'),
        'iOS_arm64': iOSTargetInfo('arm64'),
        'iOS_i386': iOSTargetInfo('i386'),
        'iOS_x86_64': iOSTargetInfo('x86_64'),
    }

    def __init__(self, options, targetsDict):
        self.source_dir = pj(options.working_dir, "SOURCE")
        build_dir = "BUILD_{}".format(options.target_platform)
        self.build_dir = pj(options.working_dir, build_dir)
        self.archive_dir = pj(options.working_dir, "ARCHIVE")
        self.toolchain_dir = pj(options.working_dir, "TOOLCHAINS")
        self.log_dir = pj(self.build_dir, 'LOGS')
        self.install_dir = pj(self.build_dir, "INSTALL")
        for d in (self.source_dir,
                  self.build_dir,
                  self.archive_dir,
                  self.toolchain_dir,
                  self.log_dir,
                  self.install_dir):
            os.makedirs(d, exist_ok=True)
        self.detect_platform()
        self.ninja_command = self._detect_ninja()
        if not self.ninja_command:
            sys.exit("ERROR: ninja command not found")
        self.meson_command = self._detect_meson()
        if not self.meson_command:
            sys.exit("ERROR: meson command not fount")
        self.mesontest_command = "meson test"
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

    def detect_platform(self):
        _platform = platform.system()
        self.distname = _platform
        if _platform == 'Windows':
            print('ERROR: kiwix-build is not intented to run on Windows platform.\n'
                  'It should probably not work, but well, you still can have a try.')
            cont = input('Do you want to continue ? [y/N]')
            if cont.lower() != 'y':
                sys.exit(0)
        if _platform == 'Darwin':
            print('WARNING: kiwix-build has not been tested on MacOS platfrom.\n'
                  'Tests, bug reports and patches are welcomed.')
        if _platform == 'Linux':
            self.distname, _, _ = platform.linux_distribution()
            self.distname = self.distname.lower()
            if self.distname == 'ubuntu':
                self.distname = 'debian'

    def setup_build(self, target_platform):
        self.platform_info = self.target_platforms[target_platform]
        if self.distname not in self.platform_info.compatible_hosts:
            print(('ERROR: The target {} cannot be build on host {}.\n'
                   'Select another target platform, or change your host system.'
                  ).format(target_platform, self.distname))
            sys.exit(-1)
        self.cross_config = self.platform_info.get_cross_config(self.distname)

    def setup_toolchains(self):
        toolchain_names = self.platform_info.toolchains
        self.toolchains =[Toolchain.all_toolchains[toolchain_name](self)
                              for toolchain_name in toolchain_names]

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

    def __getattr__(self, name):
        return getattr(self.options, name)

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

        bin_dirs = []
        if cross_compile_env:
            for k, v in self.cross_config.get('env', {}).items():
                if k.startswith('_format_'):
                    v = v.format(**self.cross_config)
                    k = k[8:]
                env[k] = v
            for toolchain in self.toolchains:
                toolchain.set_env(env)
        if cross_compile_compiler:
            for toolchain in self.toolchains:
                toolchain.set_compiler(env)
        if cross_compile_path:
            for tlc in self.toolchains:
                bin_dirs += tlc.get_bin_dir()

        pkgconfig_path = pj(self.install_dir, self.libprefix, 'pkgconfig')
        env['PKG_CONFIG_PATH'] = ':'.join([env['PKG_CONFIG_PATH'], pkgconfig_path])

        # Add ccache path
        for p in ('/usr/lib/ccache', '/usr/lib64/ccache'):
            if os.path.isdir(p):
                ccache_path = [p]
                break
        else:
            ccache_path = []
        env['PATH'] = ':'.join(bin_dirs +
                               [pj(self.install_dir, 'bin')] +
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

    def download(self, what, where=None):
        where = where or self.archive_dir
        download_remote(what, where, not self.options.no_cert_check)

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
        if os.path.exists(autoskip_file):
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

class _MetaToolchain(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name != 'Toolchain':
            Toolchain.all_toolchains[name] = _class
        return _class


class Toolchain(metaclass=_MetaToolchain):
    all_toolchains = {}
    configure_option = ""
    cmake_option = ""
    exec_wrapper_def = ""
    Builder = None
    Source = None

    def __init__(self, buildEnv):
        self.buildEnv = buildEnv
        self.source = self.Source(self) if self.Source else None
        self.builder = self.Builder(self) if self.Builder else None

    @property
    def full_name(self):
        return "{name}-{version}".format(
            name = self.name,
            version = self.version)

    @property
    def source_path(self):
        return pj(self.buildEnv.source_dir, self.source.source_dir)

    @property
    def _log_dir(self):
        return self.buildEnv.log_dir

    def set_env(self, env):
        pass

    def set_compiler(self, env):
        pass

    def command(self, name, function, *args):
        print("  {} {} : ".format(name, self.name), end="", flush=True)
        log = pj(self._log_dir, 'cmd_{}_{}.log'.format(name, self.name))
        context = Context(name, log, True)
        try:
            ret = function(*args, context=context)
            context._finalise()
            print("OK")
            return ret
        except SkipCommand:
            print("SKIP")
        except subprocess.CalledProcessError:
            print("ERROR")
            try:
                with open(log, 'r') as f:
                    print(f.read())
            except:
                pass
            raise StopBuild()
        except:
            print("ERROR")
            raise


class mingw32_toolchain(Toolchain):
    name = 'mingw32'
    arch_full = 'i686-w64-mingw32'

    @property
    def root_path(self):
        return self.buildEnv.cross_config['root_path']

    @property
    def binaries(self):
        return {k:which('{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'))
               }

    @property
    def exec_wrapper_def(self):
        try:
            which('wine')
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exec_wrapper = 'wine'"


    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['LIBS'] = " ".join(self.buildEnv.cross_config['extra_libs']) + " " +env['LIBS']

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v


class android_ndk(Toolchain):
    name = 'android-ndk'
    version = 'r13b'
    gccver = '4.9.x'

    @property
    def api(self):
        return '21' if self.arch in ('arm64', 'mips64', 'x86_64') else '14'

    @property
    def platform(self):
        return 'android-'+self.api

    @property
    def arch(self):
        return self.buildEnv.platform_info.arch

    @property
    def arch_full(self):
        return self.buildEnv.platform_info.arch_full

    @property
    def toolchain(self):
        return self.arch_full+"-4.9"

    @property
    def root_path(self):
        return pj(self.builder.install_path, 'sysroot')

    @property
    def binaries(self):
        binaries = ((k,'{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'),
                             ('LD', 'ld'))
               )
        return {k:pj(self.builder.install_path, 'bin', v)
                for k,v in binaries}

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    @property
    def full_name(self):
        return "{name}-{version}-{arch}-{api}".format(
            name = self.name,
            version = self.version,
            arch = self.arch,
            api = self.api)

    class Source(ReleaseDownload):
        archive = Remotefile('android-ndk-r13b-linux-x86_64.zip',
                             '3524d7f8fca6dc0d8e7073a7ab7f76888780a22841a6641927123146c3ffd29c',
                             'https://dl.google.com/android/repository/android-ndk-r13b-linux-x86_64.zip')

        @property
        def source_dir(self):
            return "{}-{}".format(
                self.target.name,
                self.target.version)


    class Builder(Builder):

        @property
        def install_path(self):
            return self.build_path

        def _build_platform(self, context):
            context.try_skip(self.build_path)
            script = pj(self.source_path, 'build/tools/make_standalone_toolchain.py')
            add_execution_right(script)
            command = '{script} --arch={arch} --api={api} --install-dir={install_dir} --force'
            command = command.format(
                script=script,
                arch=self.target.arch,
                api=self.target.api,
                install_dir=self.install_path
            )
            self.buildEnv.run_command(command, self.build_path, context)

        def _fix_permission_right(self, context):
            context.try_skip(self.build_path)
            bin_dirs = [pj(self.install_path, 'bin'),
                        pj(self.install_path, self.target.arch_full, 'bin'),
                        pj(self.install_path, 'libexec', 'gcc', self.target.arch_full, self.target.gccver)
                       ]
            for root, dirs, files in os.walk(self.install_path):
                if not root in bin_dirs:
                    continue

                for file_ in files:
                    file_path = pj(root, file_)
                    if os.path.islink(file_path):
                        continue
                    add_execution_right(file_path)

        def build(self):
            self.command('build_platform', self._build_platform)
            self.command('fix_permission_right', self._fix_permission_right)

    def get_bin_dir(self):
        return [pj(self.builder.install_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(self.root_path) + env['CFLAGS']
        env['CXXFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(self.root_path) + env['CXXFLAGS']
        env['LDFLAGS'] = '--sysroot={} '.format(self.root_path) + env['LDFLAGS']
        #env['CFLAGS'] = ' -fPIC -D_FILE_OFFSET_BITS=64 -O3 '+env['CFLAGS']
        #env['CXXFLAGS'] = (' -D__OPTIMIZE__ -fno-strict-aliasing '
        #                   ' -DU_HAVE_NL_LANGINFO_CODESET=0 '
        #                   '-DU_STATIC_IMPLEMENTATION -O3 '
        #                   '-DU_HAVE_STD_STRING -DU_TIMEZONE=0 ')+env['CXXFLAGS']
        env['NDK_DEBUG'] = '0'

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']


class android_sdk(Toolchain):
    name = 'android-sdk'
    version = 'r25.2.3'

    class Source(ReleaseDownload):
        archive = Remotefile('tools_r25.2.3-linux.zip',
                             '1b35bcb94e9a686dff6460c8bca903aa0281c6696001067f34ec00093145b560',
                             'https://dl.google.com/android/repository/tools_r25.2.3-linux.zip')

    class Builder(Builder):

        @property
        def install_path(self):
            return pj(self.buildEnv.toolchain_dir, self.target.full_name)

        def _build_platform(self, context):
            context.try_skip(self.install_path)
            tools_dir = pj(self.install_path, 'tools')
            shutil.copytree(self.source_path, tools_dir)
            script = pj(tools_dir, 'android')
            command = '{script} --verbose update sdk -a --no-ui --filter {packages}'
            command = command.format(
                script=script,
                packages = ','.join(str(i) for i in [1,2,8,34,162])
            )
            # packages correspond to :
            # - 1 : Android SDK Tools, revision 25.2.5
            # - 2 : Android SDK Platform-tools, revision 25.0.3
            # - 8 : Android SDK Build-tools, revision 24.0.1
            # - 34 : SDK Platform Android 7.0, API 24, revision 2
            # - 162 : Android Support Repository, revision 44
            self.buildEnv.run_command(command, self.install_path, context, input="y\n")

        def _fix_licenses(self, context):
            context.try_skip(self.install_path)
            os.makedirs(pj(self.install_path, 'licenses'), exist_ok=True)
            with open(pj(self.install_path, 'licenses', 'android-sdk-license'), 'w') as f:
                f.write("\n8933bad161af4178b1185d1a37fbf41ea5269c55\nd56f5187479451eabf01fb78af6dfcb131a6481e")

        def build(self):
            self.command('build_platform', self._build_platform)
            self.command('fix_licenses', self._fix_licenses)

    def get_bin_dir(self):
        return []

    def set_env(self, env):
        env['ANDROID_HOME'] = self.builder.install_path


class armhf_toolchain(Toolchain):
    name = 'armhf'
    arch_full = 'arm-linux-gnueabihf'

    class Source(GitClone):
        git_remote = "https://github.com/raspberrypi/tools"
        git_dir = "raspberrypi-tools"

    @property
    def root_path(self):
        return pj(self.source_path, 'arm-bcm2708', 'gcc-linaro-arm-linux-gnueabihf-raspbian-x64')

    @property
    def binaries(self):
        binaries = ((k,'{}-{}'.format(self.arch_full, v))
                for k, v in (('CC', 'gcc'),
                             ('CXX', 'g++'),
                             ('AR', 'ar'),
                             ('STRIP', 'strip'),
                             ('WINDRES', 'windres'),
                             ('RANLIB', 'ranlib'),
                             ('LD', 'ld'))
               )
        return {k:pj(self.root_path, 'bin', v)
                for k,v in binaries}

    @property
    def exec_wrapper_def(self):
        try:
            which('qemu-arm')
        except subprocess.CalledProcessError:
            return ""
        else:
            return "exec_wrapper = 'qemu-arm'"

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = " -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CFLAGS']
        env['CXXFLAGS'] = " -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CXXFLAGS']
        env['LIBS'] = " ".join(self.buildEnv.cross_config['extra_libs']) + " " +env['LIBS']
        env['QEMU_LD_PREFIX'] = pj(self.root_path, "arm-linux-gnueabihf", "libc")
        env['QEMU_SET_ENV'] = "LD_LIBRARY_PATH={}".format(
            ':'.join([
                pj(self.root_path, "arm-linux-gnueabihf", "lib"),
                pj(self.buildEnv.install_dir, 'lib'),
                pj(self.buildEnv.install_dir, self.buildEnv.libprefix)
        ]))

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']


class iOS_sdk(Toolchain):
    @property
    def root_path(self):
        return self.buildEnv.platform_info.root_path

    @property
    def binaries(self):
        return {
            'CC': xrun_find('clang'),
            'CXX': xrun_find('clang++'),
            'AR': '/usr/bin/ar',
            'STRIP': '/usr/bin/strip',
            'RANLIB': '/usr/bin/ranlib',
            'LD': '/usr/bin/ld',
        }
     
    @property
    def configure_option(self):
        return '--host=arm-apple-darwin'

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        arch = self.buildEnv.platform_info.arch
        env['CFLAGS'] = " -fembed-bitcode -isysroot {SDKROOT} -arch {arch} -miphoneos-version-min=9.0 ".format(SDKROOT=self.root_path, arch=arch) + env['CFLAGS']
        env['CXXFLAGS'] = env['CFLAGS'] + " -stdlib=libc++ -std=c++11 "+env['CXXFLAGS']
        env['LDFLAGS'] = " -arch {arch} -isysroot {SDKROOT} ".format(SDKROOT=self.root_path, arch=arch)
        env['MACOSX_DEPLOYMENT_TARGET'] = "10.4"

    def set_compiler(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']


class Builder:
    def __init__(self, options):
        self.options = options
        self.targets = OrderedDict()
        self.buildEnv = buildEnv = BuildEnv(options, self.targets)

        _targets = {}
        targetDef = options.targets
        self.add_targets(targetDef, _targets)
        dependencies = self.order_dependencies(_targets, targetDef)
        dependencies = list(remove_duplicates(dependencies))

        for dep in dependencies:
            if self.options.build_deps_only and dep == targetDef:
                continue
            self.targets[dep] = _targets[dep]

    def add_targets(self, targetName, targets):
        if targetName in targets:
            return
        targetClass = Dependency.all_deps[targetName]
        target = targetClass(self.buildEnv)
        targets[targetName] = target
        for dep in target.dependencies:
            self.add_targets(dep, targets)

    def order_dependencies(self, _targets, targetName):
        target = _targets[targetName]
        for depName in target.dependencies:
            yield from self.order_dependencies(_targets, depName)
        yield targetName

    def prepare_sources(self):
        if self.options.skip_source_prepare:
            print("SKIP")
            return

        toolchain_sources = (tlc.source for tlc in self.buildEnv.toolchains if tlc.source)
        for toolchain_source in toolchain_sources:
            print("prepare sources for toolchain {} :".format(toolchain_source.name))
            toolchain_source.prepare()

        sources = (dep.source for dep in self.targets.values() if not dep.skip)
        sources = remove_duplicates(sources, lambda s: s.__class__)
        for source in sources:
            print("prepare sources {} :".format(source.name))
            source.prepare()

    def build(self):
        toolchain_builders = (tlc.builder for tlc in self.buildEnv.toolchains if tlc.builder)
        for toolchain_builder in toolchain_builders:
            print("build toolchain {} :".format(toolchain_builder.name))
            toolchain_builder.build()

        builders = (dep.builder for dep in self.targets.values() if (dep.builder and not dep.skip))
        for builder in builders:
            if self.options.make_dist and builder.name == self.options.targets:
                continue
            print("build {} :".format(builder.name))
            builder.build()

        if self.options.make_dist:
            dep = self.targets[self.options.targets]
            builder = dep.builder
            print("make dist {}:".format(builder.name))
            builder.make_dist()

    def run(self):
        try:
            print("[INSTALL PACKAGES]")
            self.buildEnv.install_packages()
            self.buildEnv.finalize_setup()
            print("[PREPARE]")
            self.prepare_sources()
            print("[BUILD]")
            self.build()
            # No error, clean intermediate file at end of build if needed.
            print("[CLEAN]")
            if self.buildEnv.options.clean_at_end:
                self.buildEnv.clean_intermediate_directories()
            else:
                print("SKIP")
        except StopBuild:
            sys.exit("Stopping build due to errors")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('targets', default='kiwix-tools', nargs='?', metavar='TARGET',
                        choices=Dependency.all_deps.keys())
    parser.add_argument('--working-dir', default=".")
    parser.add_argument('--libprefix', default=None)
    parser.add_argument('--target-platform', default="native_dyn", choices=BuildEnv.target_platforms)
    parser.add_argument('--verbose', '-v', action="store_true",
                        help=("Print all logs on stdout instead of in specific"
                              " log files per commands"))
    parser.add_argument('--hide-progress', action='store_false', dest='show_progress',
                        help="Hide intermediate progress information.")
    parser.add_argument('--skip-source-prepare', action='store_true',
                        help="Skip the source download part")
    parser.add_argument('--build-deps-only', action='store_true',
                        help="Build only the dependencies of the specified targets.")
    parser.add_argument('--make-dist', action='store_true',
                        help="Build distrubution (dist) source archive")
    parser.add_argument('--make-release', action='store_true',
                        help="Build a release version")
    subgroup = parser.add_argument_group('advanced')
    subgroup.add_argument('--no-cert-check', action='store_true',
                          help="Skip SSL certificate verification during download")
    subgroup.add_argument('--clean-at-end', action='store_true',
                          help="Clean all intermediate files after the (successfull) build")
    subgroup = parser.add_argument_group('custom app',
                                         description="Android custom app specific options")
    subgroup.add_argument('--android-custom-app',
                          help="The custom android app to build")
    subgroup.add_argument('--zim-file-url',
                          help="The url of the zim file to download")
    subgroup.add_argument('--zim-file-size',
                          help="The size of the zim file.")
    options = parser.parse_args()

    if options.targets == 'kiwix-android-custom':
        err = False
        if not options.android_custom_app:
            print("You need to specify ANDROID_CUSTOM_APP if you "
                  "want to build a kiwix-android-custom target")
            err = True
        if not options.zim_file_url and not options.zim_file_size:
            print("You need to specify ZIM_FILE_SIZE or ZIM_FILE_URL if you "
                  "want to build a kiwix-android-custom target")
            err = True
        if err:
            sys.exit(1)
    return options


if __name__ == "__main__":
    options = parse_args()
    options.working_dir = os.path.abspath(options.working_dir)
    setup_print_progress(options.show_progress)
    builder = Builder(options)
    builder.run()
