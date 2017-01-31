#!/usr/bin/env python3

import os, sys, stat
import argparse
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


PACKAGE_NAME_MAPPERS = {
    'fedora_native_dyn': {
        'COMMON' : ['gcc-c++', 'cmake', 'automake'],
        'uuid': ['libuuid-devel'],
        'xapian-core' : None, # Not the right version on fedora 25
        'ctpp2' : None,
        'pugixml' : None, # ['pugixml-devel'] but package doesn't provide pkg-config file
        'libmicrohttpd' : ['libmicrohttpd-devel'],
        'icu4c': None,
        'zimlib': None,
    },
    'fedora_native_static' : {
        'COMMON' : ['gcc-c++', 'cmake', 'automake', 'glibc-static', 'libstdc++-static'],
        # Either there is no packages, or no static or too old
    },
    'fedora_win32_dyn' : {
        'COMMON' : ['mingw32-gcc-c++', 'mingw32-zlib', 'mingw32-bzip2', 'mingw32-win-iconv', 'mingw32-winpthreads', 'wine'],
        'libmicrohttpd' : ['mingw32-libmicrohttpd'],
    },
    'fedora_win32_static' : {
        'COMMON' : ['mingw32-gcc-c++', 'mingw32-zlib-static', 'mingw32-bzip2-static', 'mingw32-win-iconv-static', 'mingw32-winpthreads-static', 'wine'],
        'libmicrohttpd' : None, # ['mingw32-libmicrohttpd-static'] packaging dependecy seems buggy, and some static lib are name libfoo.dll.a and
                                # gcc cannot found them.
    },
    'Ubuntu_native_dyn' : {
        'COMMON' : ['gcc-5', 'cmake', 'libbz2-dev'],
        'uuid' : ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
        'libmicrohttpd' : ['libmicrohttpd-dev']
    },
    'Ubuntu_native_static' : {
        'COMMON' : ['gcc-5', 'cmake', 'libbz2-dev'],
        'uuid' : ['uuid-dev'],
        'ctpp2': ['libctpp2-dev'],
    },
}

class Defaultdict(defaultdict):
    def __getattr__(self, name):
        return self[name]

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

    _targets_env = {
        'native' : {},
        'win32'  : {'wrapper': 'mingw32-env'}
    }

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
        self.setup_build_target(options.build_target)
        self.ninja_command = self._detect_ninja()
        self.meson_command = self._detect_meson()
        self.options = options
        self.libprefix = options.libprefix or self._detect_libdir()
        self.targetsDict = targetsDict

    def detect_platform(self):
        _platform = platform.system()
        if _platform != 'Linux':
            sys.exit('ERROR: kiwix-build is intented to run only on Linux platform')
        self.distname, self.distversion, _ = platform.dist()

    def setup_build_target(self, build_target):
        self.build_target = build_target
        self.target_env = self._targets_env[self.build_target]
        getattr(self, 'setup_{}'.format(self.build_target))()

    def setup_native(self):
        self.wrapper = None
        self.cmake_command = "cmake"
        self.configure_option = ""
        self.cmake_option = ""
        self.meson_crossfile = None

    def _get_rpm_mingw32(self, value):
        command = "rpm --eval %{{mingw32_{}}}".format(value)
        output = subprocess.check_output(command, shell=True)
        return output[:-1].decode()

    def _gen_meson_crossfile(self):
        self.meson_crossfile = pj(self.build_dir, 'cross_file.txt')
        config = configparser.ConfigParser()
        config['binaries'] = {
            'c' : repr(self._get_rpm_mingw32('cc')),
            'cpp' : repr(self._get_rpm_mingw32('cxx')),
            'ar' : repr(self._get_rpm_mingw32('ar')),
            'strip' : repr(self._get_rpm_mingw32('strip')),
            'pkgconfig' : repr(self._get_rpm_mingw32('pkg_config')),
            'exe_wrapper' : repr('wine') # A command used to run generated executables.
        }
        config['properties'] = {
            'c_link_args': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4'],
            'cpp_link_args': ['-lwinmm', '-lws2_32', '-lshlwapi', '-lrpcrt4']
        }
        config['host_machine'] = {
            'system' : repr('windows'),
            'cpu_family' : repr('x86'),
            'cpu' : repr('i586'),
            'endian' : repr('little')
        }
        with open(self.meson_crossfile, 'w') as configfile:
            config.write(configfile)

    def setup_win32(self):
        command = "rpm --eval %{mingw32_env}"
        self.wrapper = pj(self.build_dir, 'mingw32-wrapper.sh')
        with open(self.wrapper, 'w') as output:
            output.write("#!/usr/bin/sh\n\n")
            output.flush()
            output.write(self._get_rpm_mingw32('env'))
            output.write('\n\nexec "$@"\n')
            output.flush()
        current_permissions = stat.S_IMODE(os.lstat(self.wrapper).st_mode)
        os.chmod(self.wrapper, current_permissions | stat.S_IXUSR)
        self.configure_option = "--host=i686-w64-mingw32"
        self.cmake_command = "mingw32-cmake"
        self.cmake_option = ""

        self._gen_meson_crossfile()

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

    def run_command(self, command, cwd, context, env=None, input=None, allow_wrapper=True):
        os.makedirs(cwd, exist_ok=True)
        if allow_wrapper and self.wrapper:
            command = "{} {}".format(self.wrapper, command)
        if env is None:
            env = dict(os.environ)
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
        urllib.request.urlretrieve(file_url, file_path)
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
        package_name_mapper = PACKAGE_NAME_MAPPERS[mapper_name]
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
    configure_option = ""
    make_option = ""
    install_option = ""
    configure_script = "configure"
    configure_env = None
    make_target = ""
    make_install_target = "install"

    def _configure(self, context):
        context.try_skip(self.build_path)
        command = "{configure_script} {configure_option} --prefix {install_dir} --libdir {libdir}"
        command = command.format(
            configure_script = pj(self.source_path, self.configure_script),
            configure_option = "{} {}".format(self.configure_option, self.buildEnv.configure_option),
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
        command = "{command} {configure_option} -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON -DCMAKE_INSTALL_PREFIX={install_dir} -DCMAKE_INSTALL_LIBDIR={libdir} {source_path}"
        command = command.format(
            command = self.buildEnv.cmake_command,
            configure_option = "{} {}".format(self.buildEnv.cmake_option, self.configure_option),
            install_dir = self.buildEnv.install_dir,
            libdir = self.buildEnv.libprefix,
            source_path = self.source_path
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
    def _gen_env(self):
        env = Defaultdict(str, os.environ)
        env['PKG_CONFIG_PATH'] = (env['PKG_CONFIG_PATH'] + ':' + pj(self.buildEnv.install_dir, self.buildEnv.libprefix, 'pkgconfig')
                                  if env['PKG_CONFIG_PATH']
                                  else pj(self.buildEnv.install_dir, self.buildEnv.libprefix, 'pkgconfig')
                                 )
        env['PATH'] = ':'.join([pj(self.buildEnv.install_dir, 'bin'), env['PATH']])
        return env

    def _configure(self, context):
        context.try_skip(self.build_path)
        if os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)
        os.makedirs(self.build_path)
        env = self._gen_env()
        if self.buildEnv.build_static:
            library_type = 'static'
        else:
            library_type = 'shared'
        configure_option = self.configure_option.format(buildEnv=self.buildEnv)
        command = "{command} --default-library={library_type} {configure_option} . {build_path} --prefix={buildEnv.install_dir} --libdir={buildEnv.libprefix} {cross_option}".format(
            command = self.buildEnv.meson_command,
            library_type=library_type,
            configure_option=configure_option,
            build_path = self.build_path,
            buildEnv=self.buildEnv,
            cross_option = "--cross-file {}".format(self.buildEnv.meson_crossfile) if self.buildEnv.meson_crossfile else ""
        )
        self.buildEnv.run_command(command, self.source_path, context, env=env, allow_wrapper=False)

    def _compile(self, context):
        env = self._gen_env()
        command = "{} -v".format(self.buildEnv.ninja_command)
        self.buildEnv.run_command(command, self.build_path, context, env=env, allow_wrapper=False)

    def _install(self, context):
        env = self._gen_env()
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

class UUID(Dependency):
    name = 'uuid'
    version = "1.42"

    class Source(ReleaseDownload):
        archive = Remotefile('e2fsprogs-1.42.tar.gz',
                             '55b46db0cec3e2eb0e5de14494a88b01ff6c0500edf8ca8927cad6da7b5e4a46')
        extract_dir = 'e2fsprogs-1.42'

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
        patches = ["xapian_pkgconfig.patch"]

    class Builder(MakeBuilder):
        configure_option = ("--enable-shared --enable-static --disable-sse "
                            "--disable-backend-inmemory --disable-documentation")
        configure_env = {'_format_LDFLAGS' : "-L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS' : "-I{buildEnv.install_dir}/include"}

    @property
    def dependencies(self):
        if self.buildEnv.build_target == 'win32':
            return []
        return ['UUID']


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
               "ctpp2_win_install_lib_in_lib_dir.patch"]

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
        configure_option = "--enable-shared --enable-static --disable-https --without-libgcrypt --without-libcurl"


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

        @property
        def configure_option(self):
            default_configure_option = "--disable-samples --disable-tests --disable-extras --disable-dyload"
            if self.buildEnv.build_static:
                default_configure_option += " --enable-static --disable-shared"
            else:
                default_configure_option += " --enable-shared --enable-shared"
            return default_configure_option


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
    dependencies = ["Kiwixlib", "MicroHttpd"]

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
            self.nativeBuildEnv.setup_build_target('native')
        else:
            self.nativeBuildEnv = buildEnv

        _targets = {}
        self.add_targets(targetDef, _targets)

        dependencies_order = list(remove_duplicates(self.order_dependencies(_targets, targetDef)))
        dependencies_order.append(targetDef)

        for dep in dependencies_order:
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
            print("[PREPARE]")
            self.prepare_sources()
            print("[BUILD]")
            self.build()
        except StopBuild:
            print("Stopping build due to errors")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('working_dir', default=".", nargs='?')
    parser.add_argument('--libprefix', default=None)
    parser.add_argument('--build-static', action="store_true")
    parser.add_argument('--build-target', default="native", choices=BuildEnv.build_targets)
    parser.add_argument('--verbose', '-v', action="store_true",
                        help=("Print all logs on stdout instead of in specific"
                              " log files per commands"))
    return parser.parse_args()

if __name__ == "__main__":
    options = parse_args()
    options.working_dir = os.path.abspath(options.working_dir)
    builder = Builder(options)
    builder.run()
