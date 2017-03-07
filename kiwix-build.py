#!/usr/bin/env python3

import os, sys, stat
import argparse
import ssl
import urllib.request
import tarfile
import subprocess
import hashlib
import shutil
import tempfile
import configparser
import platform
from collections import defaultdict, namedtuple, OrderedDict


pj = os.path.join

REMOTE_PREFIX = 'http://download.kiwix.org/dev/'

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

CROSS_ENV = {
    'fedora_win32' : {
        'root_path' : '/usr/i686-w64-mingw32/sys-root/mingw',
        'binaries' : {
            'c' : 'i686-w64-mingw32-gcc',
            'cpp' : 'i686-w64-mingw32-g++',
            'ar' : 'i686-w64-mingw32-ar',
            'strip' : 'i686-w64-mingw32-strip',
            'windres' : 'i686-w64-mingw32-windres',
            'ranlib'  : 'i686-w64-mingw32-ranlib',
            'exe_wrapper' : 'wine'
        },
        'properties' : {
            'c_link_args': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4'],
            'cpp_link_args': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4']
        },
        'host_machine' : {
            'system' : 'windows',
            'cpu_family' : 'x86',
            'cpu' : 'i686',
            'endian' : 'little'
        },
        'env': {
            '_format_PKG_CONFIG_LIBDIR' : '{root_path}/lib/pkgconfig'
        }
    },
    'debian_win32' : {
        'root_path' : '/usr/i686-w64-mingw32/',
        'binaries' : {
            'c' : 'i686-w64-mingw32-gcc',
            'cpp' : 'i686-w64-mingw32-g++',
            'ar' : 'i686-w64-mingw32-ar',
            'strip' : 'i686-w64-mingw32-strip',
            'windres' : 'i686-w64-mingw32-windres',
            'ranlib'  : 'i686-w64-mingw32-ranlib',
            'exe_wrapper' : 'wine'
        },
        'properties' : {
            'c_link_args': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4'],
            'cpp_link_args': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4']
        },
        'host_machine' : {
            'system' : 'windows',
            'cpu_family' : 'x86',
            'cpu' : 'i686',
            'endian' : 'little'
        },
        'env': {
            '_format_PKG_CONFIG_LIBDIR' : '{root_path}/lib/pkgconfig'
        }
    }
}


PACKAGE_NAME_MAPPERS = {
    'fedora_native_dyn': {
        'COMMON' : ['gcc-c++', 'cmake', 'automake'],
        'uuid': ['libuuid-devel'],
        'xapian-core' : None, # Not the right version on fedora 25
        'ctpp2' : None,
        'pugixml' : None, # ['pugixml-devel'] but package doesn't provide pkg-config file
        'libmicrohttpd' : ['libmicrohttpd-devel'],
        'zlib' : ['zlib-devel'],
        'icu4c': None,
        'zimlib': None,
    },
    'fedora_native_static' : {
        'COMMON' : ['gcc-c++', 'cmake', 'automake', 'glibc-static', 'libstdc++-static'],
        'zlib' : ['zlib-devel', 'zlib-static']
        # Either there is no packages, or no static or too old
    },
    'fedora_win32_dyn' : {
        'COMMON' : ['mingw32-gcc-c++', 'mingw32-bzip2', 'mingw32-win-iconv', 'mingw32-winpthreads', 'wine'],
        'zlib' : ['mingw32-zlib'],
        'libmicrohttpd' : ['mingw32-libmicrohttpd'],
    },
    'fedora_win32_static' : {
        'COMMON' : ['mingw32-gcc-c++', 'mingw32-bzip2-static', 'mingw32-win-iconv-static', 'mingw32-winpthreads-static', 'wine'],
        'zlib' : ['mingw32-zlib-static'],
        'libmicrohttpd' : None, # ['mingw32-libmicrohttpd-static'] packaging dependecy seems buggy, and some static lib are name libfoo.dll.a and
                                # gcc cannot found them.
    },
    'debian_native_dyn' : {
        'COMMON' : ['gcc', 'cmake', 'libbz2-dev'],
        'zlib' : ['zlib1g-dev'],
        'uuid' : ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
        'libmicrohttpd' : ['libmicrohttpd-dev']
    },
    'debian_native_static' : {
        'COMMON' : ['gcc', 'cmake', 'libbz2-dev'],
        'zlib' : ['zlib1g-dev'],
        'uuid' : ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
    },
    'debian_win32_dyn' : {
        'COMMON' : ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools']
    },
    'debian_win32_static' : {
        'COMMON' : ['g++-mingw-w64-i686', 'gcc-mingw-w64-i686', 'gcc-mingw-w64-base', 'mingw-w64-tools']
    },
}

class Defaultdict(defaultdict):
    def __getattr__(self, name):
        return self[name]


class Which():
    def __getattr__(self, name):
        command = "which {}".format(name)
        output = subprocess.check_output(command, shell=True)
        return output[:-1].decode()

    def __format__(self, format_spec):
        return getattr(self, format_spec)

def remove_duplicates(iterable, key_function=None):
    seen = set()
    if key_function is None:
        key_function = lambda e:e
    for elem in iterable:
        key = key_function(elem)
        if key in seen:
            continue
        seen.add(key)
        yield elem

def get_sha256(path):
    sha256 = hashlib.sha256()
    with open(path, 'br') as f:
        sha256.update(f.read())
    return sha256.hexdigest()

class SkipCommand(Exception):
    pass

class StopBuild(Exception):
    pass

class Remotefile(namedtuple('Remotefile', ('name', 'sha256', 'url'))):
    def __new__(cls, name, sha256, url=None):
        return super().__new__(cls, name, sha256, url)

class Context:
    def __init__(self, command_name, log_file):
        self.command_name = command_name
        self.log_file = log_file
        self.autoskip_file = None

    def try_skip(self, path):
        self.autoskip_file = pj(path, ".{}_ok".format(self.command_name))
        if os.path.exists(self.autoskip_file):
            raise SkipCommand()

    def _finalise(self):
        if self.autoskip_file is not None:
            with open(self.autoskip_file, 'w') as f: pass


def extract_archive(archive_path, dest_dir, topdir=None, name=None):
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        if not topdir:
            for d in (m for m in members if m.isdir()):
                if not os.path.dirname(d.name):
                    if topdir:
                        # There is already a top dir.
                        # Two topdirs in the same archive.
                        # Extract all
                        topdir = None
                        break
                    topdir = d
        else:
            topdir = archive.getmember(topdir)
        if topdir:
            members_to_extract = [m for m in members if m.name.startswith(topdir.name+'/')]
            os.makedirs(dest_dir, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=os.path.basename(archive_path), dir=dest_dir) as tmpdir:
                archive.extractall(path=tmpdir, members=members_to_extract)
                name = name or topdir.name
                os.rename(pj(tmpdir, topdir.name), pj(dest_dir, name))
        else:
            if name:
                dest_dir = pj(dest_dir, name)
                os.makedirs(dest_dir)
            archive.extractall(path=dest_dir)


class BuildEnv:
    build_targets = ['native', 'win32']

    def __init__(self, options, targetsDict):
        self.source_dir = pj(options.working_dir, "SOURCE")
        build_dir = "BUILD_{target}_{libmod}".format(
            target=options.build_target,
            libmod='static' if options.build_static else 'dyn'
        )
        self.build_dir = pj(options.working_dir, build_dir)
        self.archive_dir = pj(options.working_dir, "ARCHIVE")
        self.log_dir = pj(options.working_dir, 'LOGS')
        self.install_dir = pj(self.build_dir, "INSTALL")
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.install_dir, exist_ok=True)
        self.detect_platform()
        self.ninja_command = self._detect_ninja()
        if not self.ninja_command:
            sys.exit("ERROR: ninja command not found")
        self.meson_command = self._detect_meson()
        if not self.meson_command:
            sys.exit("ERROR: meson command not fount")
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
            if self.distname == 'Ubuntu':
                self.distname = 'debian'

    def finalize_setup(self):
        getattr(self, 'setup_{}'.format(self.build_target))()

    def setup_native(self):
        self.cross_env = {}
        self.wrapper = None
        self.configure_option = ""
        self.cmake_option = ""
        self.cmake_crossfile = None
        self.meson_crossfile = None

    def _gen_crossfile(self, name):
        crossfile = pj(self.build_dir, name)
        template_file = pj(SCRIPT_DIR, 'templates', name)
        with open(template_file, 'r') as f:
            template = f.read()
        content = template.format(
            which=Which(),
            **self.cross_env
        )
        with open(crossfile, 'w') as outfile:
            outfile.write(content)
        return crossfile

    def setup_win32(self):
        cross_name = "{host}_{target}".format(
            host = self.distname,
            target = self.build_target)
        try:
            self.cross_env = CROSS_ENV[cross_name]
        except KeyError:
            sys.exit("ERROR : We don't know how to set env to compile"
                     " a {target} version on a {host} host.".format(
                        target = self.build_target,
                        host = self.distname
                    ))

        self.wrapper = self._gen_crossfile('bash_wrapper.sh')
        current_permissions = stat.S_IMODE(os.lstat(self.wrapper).st_mode)
        os.chmod(self.wrapper, current_permissions | stat.S_IXUSR)
        self.configure_option = "--host=i686-w64-mingw32"
        self.cmake_option = ""
        self.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
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

    def _set_env(self, env):
        if env is None:
            env = Defaultdict(str, os.environ)
        for k, v in self.cross_env.get('env', {}).items():
            if k.startswith('_format_'):
                v = v.format(**self.cross_env)
                k = k[8:]
            env[k] = v
        pkgconfig_path = pj(self.install_dir, self.libprefix, 'pkgconfig')
        env['PKG_CONFIG_PATH'] = (env['PKG_CONFIG_PATH'] + ':' + pkgconfig_path
                                  if env['PKG_CONFIG_PATH']
                                  else pkgconfig_path
                                 )
        env['PATH'] = ':'.join([pj(self.install_dir, 'bin'), env['PATH']])
        ld_library_path = ':'.join([
            pj(self.install_dir, 'lib'),
            pj(self.install_dir, 'lib64')
        ])
        env['LD_LIBRARY_PATH'] = (env['LD_LIBRARY_PATH'] + ':' + ld_library_path
                                  if env['LD_LIBRARY_PATH']
                                  else ld_library_path
                                 )
        env['CPPFLAGS'] = '-I'+pj(self.install_dir, 'include')
        env['LDFLAGS'] = '-L'+pj(self.install_dir, 'lib')
        return env

    def run_command(self, command, cwd, context, env=None, input=None, allow_wrapper=True):
        os.makedirs(cwd, exist_ok=True)
        if allow_wrapper and self.wrapper:
            command = "{} {}".format(self.wrapper, command)
        env = self._set_env(env)
        log = None
        try:
            if not self.options.verbose:
                log = open(context.log_file, 'w')
            print("run command '{}'".format(command), file=log)
            print("env is :",file=log)
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
            package_installer = 'dnf'
        elif self.distname in ('debian', 'Ubuntu'):
            package_installer = 'apt-get'
        mapper_name = "{host}_{target}_{build_type}".format(
            host = self.distname,
            target = self.build_target,
            build_type = 'static' if self.options.build_static else 'dyn')
        try:
            package_name_mapper = PACKAGE_NAME_MAPPERS[mapper_name]
        except KeyError:
            print("SKIP : We don't know which packages we must install to compile"
                  " a {target} {build_type} version on a {host} host.".format(
                      target = self.build_target,
                      build_type = 'static' if self.options.build_static else 'dyn',
                      host = self.distname
                 ))
            return

        packages_list = package_name_mapper.get('COMMON', [])
        for dep in self.targetsDict.values():
            packages = package_name_mapper.get(dep.name)
            if packages:
                packages_list += packages
                dep.skip = True
        if os.path.exists(autoskip_file):
            print("SKIP")
            return
        if packages_list:
            command = "sudo {package_installer} install {packages_list}".format(
                package_installer = package_installer,
                packages_list = " ".join(packages_list)
            )
            print(command)
            subprocess.check_call(command, shell=True)
        else:
            print("SKIP, No package to install.")

        with open(autoskip_file, 'w') as f: pass

################################################################################
##### PROJECT
################################################################################
class _MetaDependency(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name != 'Dependency':
            Dependency.all_deps[name] = _class
        return _class


class Dependency(metaclass=_MetaDependency):
    all_deps = {}
    dependencies = []
    force_native_build = False
    version = None
    def __init__(self, buildEnv):
        self.buildEnv = buildEnv
        self.source = self.Source(self)
        self.builder = self.Builder(self)
        self.skip = False

    @property
    def full_name(self):
        if self.version:
            return "{}-{}".format(self.name, self.version)
        return self.name

    @property
    def source_path(self):
        return pj(self.buildEnv.source_dir, self.source.source_dir)

    @property
    def _log_dir(self):
        return self.buildEnv.log_dir

    def command(self, name, function, *args):
        print("  {} {} : ".format(name, self.name), end="", flush=True)
        log = pj(self._log_dir, 'cmd_{}_{}.log'.format(name, self.name))
        context = Context(name, log)
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


class Source:
    """Base Class to the real preparator
       A source preparator must install source in the self.source_dir attribute
       inside the buildEnv.source_dir."""
    def __init__(self, target):
        self.target = target
        self.buildEnv = target.buildEnv

    @property
    def name(self):
        return self.target.name

    @property
    def source_dir(self):
        return self.target.full_name

    def command(self, *args, **kwargs):
        return self.target.command(*args, **kwargs)


class ReleaseDownload(Source):
    archive_top_dir = None
    @property
    def extract_path(self):
        return pj(self.buildEnv.source_dir, self.source_dir)

    def _download(self, context):
        self.buildEnv.download(self.archive)

    def _extract(self, context):
        context.try_skip(self.extract_path)
        if os.path.exists(self.extract_path):
            shutil.rmtree(self.extract_path)
        extract_archive(pj(self.buildEnv.archive_dir, self.archive.name),
                           self.buildEnv.source_dir,
                           topdir=self.archive_top_dir,
                           name=self.source_dir)

    def _patch(self, context):
        context.try_skip(self.extract_path)
        for p in self.patches:
            with open(pj(SCRIPT_DIR, 'patches', p), 'r') as patch_input:
                self.buildEnv.run_command("patch -p1", self.extract_path, context, input=patch_input, allow_wrapper=False)

    def prepare(self):
        self.command('download', self._download)
        self.command('extract', self._extract)
        if hasattr(self, 'patches'):
            self.command('patch', self._patch)


class GitClone(Source):
    git_ref = "master"
    @property
    def source_dir(self):
        return self.git_dir

    @property
    def git_path(self):
        return pj(self.buildEnv.source_dir, self.git_dir)

    def _git_clone(self, context):
        if os.path.exists(self.git_path):
            raise SkipCommand()
        command = "git clone " + self.git_remote
        self.buildEnv.run_command(command, self.buildEnv.source_dir, context)

    def _git_update(self, context):
        self.buildEnv.run_command("git fetch", self.git_path, context)
        self.buildEnv.run_command("git checkout "+self.git_ref, self.git_path, context)

    def prepare(self):
        self.command('gitclone', self._git_clone)
        self.command('gitupdate', self._git_update)


class Builder:
    subsource_dir = None
    def __init__(self, target):
        self.target = target
        self.buildEnv = target.buildEnv

    @property
    def name(self):
        return self.target.name

    @property
    def source_path(self):
        base_source_path = self.target.source_path
        if self.subsource_dir:
            return pj(base_source_path, self.subsource_dir)
        return base_source_path

    @property
    def build_path(self):
        return pj(self.buildEnv.build_dir, self.target.full_name)

    def command(self, *args, **kwargs):
        return self.target.command(*args, **kwargs)

    def build(self):
        self.command('configure', self._configure)
        self.command('compile', self._compile)
        self.command('install', self._install)


class MakeBuilder(Builder):
    configure_option = static_configure_option = dynamic_configure_option = ""
    make_option = ""
    install_option = ""
    configure_script = "configure"
    configure_env = None
    make_target = ""
    make_install_target = "install"

    def _configure(self, context):
        context.try_skip(self.build_path)
        configure_option = "{} {} {}".format(
            self.configure_option,
            self.static_configure_option if self.buildEnv.build_static else self.dynamic_configure_option,
            self.buildEnv.configure_option)
        command = "{configure_script} {configure_option} --prefix {install_dir} --libdir {libdir}"
        command = command.format(
            configure_script = pj(self.source_path, self.configure_script),
            configure_option = configure_option,
            install_dir = self.buildEnv.install_dir,
            libdir = pj(self.buildEnv.install_dir, self.buildEnv.libprefix)
        )
        env = Defaultdict(str, os.environ)
        if self.buildEnv.build_static:
            env['CFLAGS'] = env['CFLAGS'] + ' -fPIC'
        if self.configure_env:
           for k in self.configure_env:
               if k.startswith('_format_'):
                   v = self.configure_env.pop(k)
                   v = v.format(buildEnv=self.buildEnv, env=env)
                   self.configure_env[k[8:]] = v
           env.update(self.configure_env)
        self.buildEnv.run_command(command, self.build_path, context, env=env)

    def _compile(self, context):
        context.try_skip(self.build_path)
        command = "make -j4 {make_target} {make_option}".format(
            make_target = self.make_target,
            make_option = self.make_option
        )
        self.buildEnv.run_command(command, self.build_path, context)

    def  _install(self, context):
        context.try_skip(self.build_path)
        command = "make {make_install_target} {make_option}".format(
            make_install_target = self.make_install_target,
            make_option = self.make_option
        )
        self.buildEnv.run_command(command, self.build_path, context)


class CMakeBuilder(MakeBuilder):
    def _configure(self, context):
        context.try_skip(self.build_path)
        command = ("cmake {configure_option}"
                   " -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON"
                   " -DCMAKE_INSTALL_PREFIX={install_dir}"
                   " -DCMAKE_INSTALL_LIBDIR={libdir}"
                   " {source_path}"
                   " {cross_option}")
        command = command.format(
            configure_option = "{} {}".format(self.buildEnv.cmake_option, self.configure_option),
            install_dir = self.buildEnv.install_dir,
            libdir = self.buildEnv.libprefix,
            source_path = self.source_path,
            cross_option = "-DCMAKE_TOOLCHAIN_FILE={}".format(self.buildEnv.cmake_crossfile) if self.buildEnv.cmake_crossfile else ""
        )
        env = Defaultdict(str, os.environ)
        if self.buildEnv.build_static:
            env['CFLAGS'] = env['CFLAGS'] + ' -fPIC'
        if self.configure_env:
           for k in self.configure_env:
               if k.startswith('_format_'):
                   v = self.configure_env.pop(k)
                   v = v.format(buildEnv=self.buildEnv, env=env)
                   self.configure_env[k[8:]] = v
           env.update(self.configure_env)
        self.buildEnv.run_command(command, self.build_path, context, env=env, allow_wrapper=False)


class MesonBuilder(Builder):
    configure_option = ""

    def _configure(self, context):
        context.try_skip(self.build_path)
        if os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)
        os.makedirs(self.build_path)
        if self.buildEnv.build_static:
            library_type = 'static'
        else:
            library_type = 'shared'
        configure_option = self.configure_option.format(buildEnv=self.buildEnv)
        command = ("{command} . {build_path}"
                   " --default-library={library_type}"
                   " {configure_option}"
                   " --prefix={buildEnv.install_dir}"
                   " --libdir={buildEnv.libprefix}"
                   " {cross_option}")
        command = command.format(
            command = self.buildEnv.meson_command,
            library_type=library_type,
            configure_option=configure_option,
            build_path = self.build_path,
            buildEnv=self.buildEnv,
            cross_option = "--cross-file {}".format(self.buildEnv.meson_crossfile) if self.buildEnv.meson_crossfile else ""
        )
        self.buildEnv.run_command(command, self.source_path, context, allow_wrapper=False)

    def _compile(self, context):
        command = "{} -v".format(self.buildEnv.ninja_command)
        self.buildEnv.run_command(command, self.build_path, context, allow_wrapper=False)

    def _install(self, context):
        command = "{} -v install".format(self.buildEnv.ninja_command)
        self.buildEnv.run_command(command, self.build_path, context, allow_wrapper=False)


# *************************************
# Missing dependencies
# Is this ok to assume that those libs
# exist in your "distri" (linux/mac) ?
# If not, we need to compile them here
# *************************************
# Zlib
# LZMA
# aria2
# Argtable
# MSVirtual
# Android
# libiconv
# gettext
# *************************************

class zlib(Dependency):
    name = 'zlib'
    version = '1.2.8'

    class Source(ReleaseDownload):
        archive = Remotefile('zlib-1.2.8.tar.gz',
                             '36658cb768a54c1d4dec43c3116c27ed893e88b02ecfcb44f2166f9c0b7f2a0d')
        patches = ['zlib_std_libname.patch']

    class Builder(CMakeBuilder):
        @property
        def configure_option(self):
            return "-DINSTALL_PKGCONFIG_DIR={}".format(pj(self.buildEnv.install_dir, self.buildEnv.libprefix, 'pkgconfig'))

class UUID(Dependency):
    name = 'uuid'
    version = "1.43.4"

    class Source(ReleaseDownload):
        archive = Remotefile('e2fsprogs-1.43.4.tar.gz',
                             '1644db4fc58300c363ba1ab688cf9ca1e46157323aee1029f8255889be4bc856',
                             'https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v1.43.4/e2fsprogs-1.43.4.tar.gz')
        extract_dir = 'e2fsprogs-1.43.4'

    class Builder(MakeBuilder):
        configure_option = "--enable-libuuid"
        configure_env = {'_format_CFLAGS' : "{env.CFLAGS} -fPIC"}
        make_target = 'libs'
        make_install_target = 'install-libs'


class Xapian(Dependency):
    name = "xapian-core"
    version = "1.4.0"

    class Source(ReleaseDownload):
        archive = Remotefile('xapian-core-1.4.0.tar.xz',
                             '10584f57112aa5e9c0e8a89e251aecbf7c582097638bfee79c1fe39a8b6a6477')
        patches = ["xapian_pkgconfig.patch",
                   "xapian_no_hardcode_lz.patch"]

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-inmemory --disable-documentation"
        dynamic_configure_option = "--enable-shared --disable-static"
        static_configure_option = "--enable-static --disable-shared"
        configure_env = {'_format_LDFLAGS' : "-L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS' : "-I{buildEnv.install_dir}/include"}

    @property
    def dependencies(self):
        deps = ['zlib']
        if self.buildEnv.build_target == 'win32':
            return deps
        return deps + ['UUID']


class CTPP2(Dependency):
    name = "ctpp2"
    version = "2.8.3"

    class Source(ReleaseDownload):
         archive = Remotefile('ctpp2-2.8.3.tar.gz',
                              'a83ffd07817adb575295ef40fbf759892512e5a63059c520f9062d9ab8fb42fc')
         patches = ["ctpp2_include.patch",
               "ctpp2_no_src_modification.patch",
               "ctpp2_fix-static-libname.patch",
               "ctpp2_mingw32.patch",
               "ctpp2_dll_export_VMExecutable.patch",
               "ctpp2_win_install_lib_in_lib_dir.patch",
               "ctpp2_iconv_support.patch"]

    class Builder(CMakeBuilder):
        configure_option = "-DMD5_SUPPORT=OFF"


class Pugixml(Dependency):
    name = "pugixml"
    version = "1.2"

    class Source(ReleaseDownload):
        archive = Remotefile('pugixml-1.2.tar.gz',
                             '0f422dad86da0a2e56a37fb2a88376aae6e931f22cc8b956978460c9db06136b')
        patches = ["pugixml_meson.patch"]

    Builder = MesonBuilder


class MicroHttpd(Dependency):
    name = "libmicrohttpd"
    version = "0.9.46"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.46.tar.gz',
                             '06dbd2654f390fa1e8196fe063fc1449a6c2ed65a38199a49bf29ad8a93b8979',
                             'http://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.46.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl"
        dynamic_configure_option = "--enable-shared --disable-static"
        static_configure_option = "--enable-static --disable-shared"


class Icu(Dependency):
    name = "icu4c"
    version = "56_1"

    class Source(ReleaseDownload):
        archive = Remotefile('icu4c-56_1-src.tgz',
                             '3a64e9105c734dcf631c0b3ed60404531bce6c0f5a64bfe1a6402a4cc2314816'
                            )
        patches = ["icu4c_fix_static_lib_name_mingw.patch"]
        data = Remotefile('icudt56l.dat',
                          'e23d85eee008f335fc49e8ef37b1bc2b222db105476111e3d16f0007d371cbca')

        def _download_data(self, context):
            self.buildEnv.download(self.data)

        def _copy_data(self, context):
            context.try_skip(self.extract_path)
            shutil.copyfile(pj(self.buildEnv.archive_dir, self.data.name), pj(self.extract_path, 'source', 'data', 'in', self.data.name))

        def prepare(self):
            super().prepare()
            self.command("download_data", self._download_data)
            self.command("copy_data", self._copy_data)

    class Builder(MakeBuilder):
        subsource_dir = "source"
        configure_option = "--disable-samples --disable-tests --disable-extras --disable-dyload"
        dynamic_configure_option = "--enable-shared --disable-static"
        static_configure_option = "--enable-static --disable-shared"


class Icu_native(Icu):
    force_native_build = True

    class Builder(Icu.Builder):
        @property
        def build_path(self):
            return super().build_path+"_native"

        def _install(self, context):
            raise SkipCommand()


class Icu_cross_compile(Icu):
    dependencies = ['Icu_native']

    class Builder(Icu.Builder):
        @property
        def configure_option(self):
            Icu_native = self.buildEnv.targetsDict['Icu_native']
            return super().configure_option + " --with-cross-build=" + Icu_native.builder.build_path


class Zimlib(Dependency):
    name = "zimlib"

    class Source(GitClone):
        #git_remote = "https://gerrit.wikimedia.org/r/p/openzim.git"
        git_remote = "https://github.com/mgautierfr/openzim"
        git_dir = "openzim"
        git_ref = "meson"

    class Builder(MesonBuilder):
        subsource_dir = "zimlib"


class Kiwixlib(Dependency):
    name = "kiwix-lib"
    dependencies = ['zlib']

    @property
    def dependencies(self):
        if self.buildEnv.build_target == 'win32':
            return ["Xapian", "CTPP2", "Pugixml", "Icu_cross_compile", "Zimlib"]
        return ["Xapian", "CTPP2", "Pugixml", "Icu", "Zimlib"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-lib.git"
        git_dir = "kiwix-lib"

    class Builder(MesonBuilder):
        configure_option = "-Dctpp2-install-prefix={buildEnv.install_dir}"


class KiwixTools(Dependency):
    name = "kiwix-tools"
    dependencies = ["Kiwixlib", "MicroHttpd", "zlib"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-tools.git"
        git_dir = "kiwix-tools"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
           base_options = "-Dctpp2-install-prefix={buildEnv.install_dir}"
           if self.buildEnv.build_static:
               base_options += " -Dstatic-linkage=true"
           return base_options


class Builder:
    def __init__(self, options, targetDef='KiwixTools'):
        self.targets = OrderedDict()
        self.buildEnv = buildEnv = BuildEnv(options, self.targets)
        if buildEnv.build_target != 'native':
            self.nativeBuildEnv = BuildEnv(options, self.targets)
            self.nativeBuildEnv.build_target = 'native'
        else:
            self.nativeBuildEnv = buildEnv

        _targets = {}
        self.add_targets(targetDef, _targets)
        dependencies = self.order_dependencies(_targets, targetDef)
        dependencies = list(remove_duplicates(dependencies))

        for dep in dependencies:
             self.targets[dep] = _targets[dep]

    def add_targets(self, targetName, targets):
        if targetName in targets:
            return
        targetClass = Dependency.all_deps[targetName]
        if targetClass.force_native_build:
            target = targetClass(self.nativeBuildEnv)
        else:
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
        sources = (dep.source for dep in self.targets.values() if not dep.skip)
        sources = remove_duplicates(sources, lambda s:s.__class__)
        for source in sources:
            print("prepare sources {} :".format(source.name))
            source.prepare()

    def build(self):
        builders = (dep.builder for dep in self.targets.values() if not dep.skip)
        for builder in builders:
            print("build {} :".format(builder.name))
            builder.build()

    def run(self):
        try:
            print("[INSTALL PACKAGES]")
            self.buildEnv.install_packages()
            self.buildEnv.finalize_setup()
            if self.nativeBuildEnv != self.buildEnv:
                self.nativeBuildEnv.finalize_setup()
            print("[PREPARE]")
            self.prepare_sources()
            print("[BUILD]")
            self.build()
        except StopBuild:
            sys.exit("Stopping build due to errors")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('working_dir', default=".", nargs='?')
    parser.add_argument('--libprefix', default=None)
    parser.add_argument('--build-static', action="store_true")
    parser.add_argument('--build-target', default="native", choices=BuildEnv.build_targets)
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
