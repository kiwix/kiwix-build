#!/usr/bin/env python3

import os, sys, stat
import argparse
import ssl
import urllib.request
import subprocess
import platform
from collections import OrderedDict

from dependencies import Dependency
from dependency_utils import ReleaseDownload, Builder
from utils import (
    pj,
    remove_duplicates,
    get_sha256,
    StopBuild,
    SkipCommand,
    Defaultdict,
    Remotefile,
    Context)

REMOTE_PREFIX = 'http://download.kiwix.org/dev/'

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

CROSS_ENV = {
    'fedora_win32': {
        'toolchain_names': ['mingw32_toolchain'],
        'root_path': '/usr/i686-w64-mingw32/sys-root/mingw',
        'extra_libs': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4', '-lmsvcr90'],
        'host_machine': {
            'system': 'windows',
            'cpu_family': 'x86',
            'cpu': 'i686',
            'endian': 'little'
        }
    },
    'fedora_android': {
        'toolchain_names': ['android_ndk'],
        'extra_libs': [],
        'host_machine': {
            'system': 'Android',
            'cpu_family': 'x86',
            'cpu': 'i686',
            'endian': 'little'
        }
    },
    'debian_win32': {
        'toolchain_names': ['mingw32_toolchain'],
        'root_path': '/usr/i686-w64-mingw32/',
        'extra_libs': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4', '-lmsvcr90'],
        'host_machine': {
            'system': 'windows',
            'cpu_family': 'x86',
            'cpu': 'i686',
            'endian': 'little'
        }
    },
    'debian_android': {
        'toolchain_names': ['android_ndk'],
        'extra_libs': [],
        'host_machine': {
            'system': 'Android',
            'cpu_family': 'x86',
            'cpu': 'i686',
            'endian': 'little'
        }
    }
}


PACKAGE_NAME_MAPPERS = {
    'fedora_native_dyn': {
        'COMMON': ['gcc-c++', 'cmake', 'automake', 'ccache'],
        'uuid': ['libuuid-devel'],
        'xapian-core': None, # Not the right version on fedora 25
        'ctpp2': None,
        'pugixml': None, # ['pugixml-devel'] but package doesn't provide pkg-config file
        'libmicrohttpd': ['libmicrohttpd-devel'],
        'zlib': ['zlib-devel'],
        'lzma': ['xz-devel'],
        'icu4c': None,
        'zimlib': None,
    },
    'fedora_native_static': {
        'COMMON': ['gcc-c++', 'cmake', 'automake', 'glibc-static', 'libstdc++-static', 'ccache'],
        'zlib': ['zlib-devel', 'zlib-static'],
        'lzma': ['xz-devel', 'xz-static']
        # Either there is no packages, or no static or too old
    },
    'fedora_win32_dyn': {
        'COMMON': ['mingw32-gcc-c++', 'mingw32-bzip2', 'mingw32-win-iconv', 'mingw32-winpthreads', 'wine', 'ccache'],
        'zlib': ['mingw32-zlib'],
        'lzma': ['mingw32-xz-libs'],
        'libmicrohttpd': ['mingw32-libmicrohttpd'],
    },
    'fedora_win32_static': {
        'COMMON': ['mingw32-gcc-c++', 'mingw32-bzip2-static', 'mingw32-win-iconv-static', 'mingw32-winpthreads-static', 'wine', 'ccache'],
        'zlib': ['mingw32-zlib-static'],
        'lzma': ['mingw32-xz-libs-static'],
        'libmicrohttpd': None, # ['mingw32-libmicrohttpd-static'] packaging dependecy seems buggy, and some static lib are name libfoo.dll.a and
                               # gcc cannot found them.
    },
    'fedora_android': {
        'COMMON': ['gcc-c++', 'cmake', 'automake', 'ccache', 'java-1.8.0-openjdk-devel']
    },
    'debian_native_dyn': {
        'COMMON': ['gcc', 'cmake', 'libbz2-dev', 'ccache'],
        'zlib': ['zlib1g-dev'],
        'uuid': ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
        'libmicrohttpd': ['libmicrohttpd-dev', 'ccache']
    },
    'debian_native_static': {
        'COMMON': ['gcc', 'cmake', 'libbz2-dev', 'ccache'],
        'zlib': ['zlib1g-dev'],
        'uuid': ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
    },
    'debian_win32_dyn': {
        'COMMON': ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools', 'ccache']
    },
    'debian_win32_static': {
        'COMMON': ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools', 'ccache']
    },
    'debian_android': {
        'COMMON': ['gcc', 'cmake', 'ccache']
    },
}


def which(name):
    command = "which {}".format(name)
    output = subprocess.check_output(command, shell=True)
    return output[:-1].decode()


class TargetInfo:
    def __init__(self, build, static):
        self.build = build
        self.static = static

    def __str__(self):
        return "{}_{}".format(self.build, 'static' if self.static else 'dyn')


class AndroidTargetInfo(TargetInfo):
    __arch_infos = {
        'arm' : ('arm-linux-androideabi'),
        'arm64': ('aarch64-linux-android'),
        'mips': ('mipsel-linux-android'),
        'mips64': ('mips64el-linux-android'),
        'x86': ('i686-linux-android'),
        'x86_64': ('x86_64-linux-android'),
    }

    def __init__(self, arch):
        super().__init__('android', True)
        self.arch = arch
        self.arch_full = self.__arch_infos[arch]

    def __str__(self):
        return "android"


class BuildEnv:
    target_platforms = {
        'native_dyn': TargetInfo('native', False),
        'native_static': TargetInfo('native', True),
        'win32_dyn': TargetInfo('win32', False),
        'win32_static': TargetInfo('win32', True),
        'android_arm': AndroidTargetInfo('arm'),
        'android_arm64': AndroidTargetInfo('arm64'),
        'android_mips': AndroidTargetInfo('mips'),
        'android_mips64': AndroidTargetInfo('mips64'),
        'android_x86': AndroidTargetInfo('x86'),
        'android_x86_64': AndroidTargetInfo('x86_64'),
    }

    def __init__(self, options, targetsDict):
        self.source_dir = pj(options.working_dir, "SOURCE")
        build_dir = "BUILD_{}".format(options.target_platform)
        self.build_dir = pj(options.working_dir, build_dir)
        self.archive_dir = pj(options.working_dir, "ARCHIVE")
        self.log_dir = pj(self.build_dir, 'LOGS')
        self.install_dir = pj(self.build_dir, "INSTALL")
        for d in (self.source_dir,
                  self.build_dir,
                  self.archive_dir,
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
        self.setup_build(options.target_platform)
        self.setup_toolchains()
        self.options = options
        self.libprefix = options.libprefix or self._detect_libdir()
        self.targetsDict = targetsDict

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
        self.platform_info = platform_info = self.target_platforms[target_platform]
        if platform_info.build == 'native':
            self.cross_env = {}
        else:
            cross_name = "{host}_{target}".format(
                host = self.distname,
                target = platform_info.build)
            try:
                self.cross_env = CROSS_ENV[cross_name]
            except KeyError:
                sys.exit("ERROR : We don't know how to set env to compile"
                         " a {target} version on a {host} host.".format(
                            target = platform_info.build,
                            host = self.distname
                        ))

    def setup_toolchains(self):
        toolchain_names = self.cross_env.get('toolchain_names', [])
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
            **self.cross_env
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

    def _set_env(self, env, cross_compile_env, cross_compile_path):
        if env is None:
            env = Defaultdict(str, os.environ)

        bin_dirs = []
        if cross_compile_env:
            for k, v in self.cross_env.get('env', {}).items():
                if k.startswith('_format_'):
                    v = v.format(**self.cross_env)
                    k = k[8:]
                env[k] = v
            for toolchain in self.toolchains:
                toolchain.set_env(env)
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
                                          pj(self.install_dir, 'lib64')
                                          ])

        env['CPPFLAGS'] = " ".join(['-I'+pj(self.install_dir, 'include'), env['CPPFLAGS']])
        env['LDFLAGS'] = " ".join(['-L'+pj(self.install_dir, 'lib'),
                                   '-L'+pj(self.install_dir, 'lib64'),
                                   env['LDFLAGS']])
        return env

    def run_command(self, command, cwd, context, env=None, input=None, cross_path_only=False):
        os.makedirs(cwd, exist_ok=True)
        cross_compile_env = True
        cross_compile_path = True
        if context.force_native_build:
            cross_compile_env = False
            cross_compile_path = False
        if cross_path_only:
            cross_compile_env = False
        env = self._set_env(env, cross_compile_env, cross_compile_path)
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
                kwargs['stdin'] = input
            return subprocess.check_call(command, shell=True, cwd=cwd, env=env, stdout=log or sys.stdout, stderr=subprocess.STDOUT, **kwargs)
        finally:
            if log:
                log.close()

    def download(self, what, where=None):
        where = where or self.archive_dir
        file_path = pj(where, what.name)
        file_url = what.url or (REMOTE_PREFIX + what.name)
        if os.path.exists(file_path):
            if what.sha256 == get_sha256(file_path):
                raise SkipCommand()
            os.remove(file_path)

        if options.no_cert_check == True:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        else:
            context = None
        batch_size = 1024 * 8
        with urllib.request.urlopen(file_url, context=context) as resource, open(file_path, 'wb') as file:
            while True:
                batch = resource.read(batch_size)
                if not batch:
                    break
                file.write(batch)

        if not what.sha256:
            print('Sha256 for {} not set, do no verify download'.format(what.name))
        elif what.sha256 != get_sha256(file_path):
            os.remove(file_path)
            raise StopBuild()

    def install_packages(self):
        autoskip_file = pj(self.build_dir, ".install_packages_ok")
        if self.distname in ('fedora', 'redhat', 'centos'):
            package_installer = 'sudo dnf install {}'
            package_checker = 'rpm -q --quiet {}'
        elif self.distname in ('debian', 'Ubuntu'):
            package_installer = 'sudo apt-get install {}'
            package_checker = 'LANG=C dpkg -s {} 2>&1 | grep Status | grep "ok installed" 1>/dev/null 2>&1'
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
        return self.buildEnv.cross_env['root_path']

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
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def get_bin_dir(self):
        return [pj(self.root_path, 'bin')]

    def set_env(self, env):
        for k, v in self.binaries.items():
            env[k] = v

        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = " -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CFLAGS']
        env['CXXFLAGS'] = " -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CXXFLAGS']
        env['LIBS'] = " ".join(self.buildEnv.cross_env['extra_libs']) + " " +env['LIBS']


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
            current_permissions = stat.S_IMODE(os.lstat(script).st_mode)
            os.chmod(script, current_permissions | stat.S_IXUSR)
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
                    current_permissions = stat.S_IMODE(os.lstat(file_path).st_mode)
                    os.chmod(file_path, current_permissions | stat.S_IXUSR)

        def build(self):
            self.command('build_platform', self._build_platform)
            self.command('fix_permission_right', self._fix_permission_right)

    def get_bin_dir(self):
        return [pj(self.builder.install_path, 'bin')]

    def set_env(self, env):
        env['CC'] = self.binaries['CC']
        env['CXX'] = self.binaries['CXX']

        env['PKG_CONFIG_LIBDIR'] = pj(self.root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(self.root_path) + env['CFLAGS']
        env['CXXFLAGS'] = '-fPIC -D_LARGEFILE64_SOURCE=1 -D_FILE_OFFSET_BITS=64 --sysroot={} '.format(self.root_path) + env['CXXFLAGS']
        env['LDFLAGS'] = ' -fPIE -pie --sysroot={} '.format(self.root_path) + env['LDFLAGS']
        #env['CFLAGS'] = ' -fPIC -D_FILE_OFFSET_BITS=64 -O3 '+env['CFLAGS']
        #env['CXXFLAGS'] = (' -D__OPTIMIZE__ -fno-strict-aliasing '
        #                   ' -DU_HAVE_NL_LANGINFO_CODESET=0 '
        #                   '-DU_STATIC_IMPLEMENTATION -O3 '
        #                   '-DU_HAVE_STD_STRING -DU_TIMEZONE=0 ')+env['CXXFLAGS']
        env['NDK_DEBUG'] = '0'


class Builder:
    def __init__(self, options):
        self.targets = OrderedDict()
        self.buildEnv = buildEnv = BuildEnv(options, self.targets)

        _targets = {}
        targetDef = options.targets
        self.add_targets(targetDef, _targets)
        dependencies = self.order_dependencies(_targets, targetDef)
        dependencies = list(remove_duplicates(dependencies))

        for dep in dependencies:
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
            print("build {} :".format(builder.name))
            builder.build()

    def run(self):
        try:
            print("[INSTALL PACKAGES]")
            self.buildEnv.install_packages()
            self.buildEnv.finalize_setup()
            print("[PREPARE]")
            self.prepare_sources()
            print("[BUILD]")
            self.build()
        except StopBuild:
            sys.exit("Stopping build due to errors")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('targets', default='KiwixTools', nargs='?')
    parser.add_argument('--working-dir', default=".")
    parser.add_argument('--libprefix', default=None)
    parser.add_argument('--target-platform', default="native_dyn", choices=BuildEnv.target_platforms)
    parser.add_argument('--verbose', '-v', action="store_true",
                        help=("Print all logs on stdout instead of in specific"
                              " log files per commands"))
    parser.add_argument('--no-cert-check', action='store_true',
                        help="Skip SSL certificate verification during download")
    return parser.parse_args()


if __name__ == "__main__":
    options = parse_args()
    options.working_dir = os.path.abspath(options.working_dir)
    builder = Builder(options)
    builder.run()
