#!/usr/bin/env python3

import os, sys
import argparse
import urllib.request
import tarfile
import subprocess
import hashlib
import shutil
import tempfile
from collections import defaultdict, namedtuple

pj = os.path.join

REMOTE_PREFIX = 'http://download.kiwix.org/dev/'

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


class Defaultdict(defaultdict):
    def __getattr__(self, name):
        return self[name]

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


def command(name):
    def decorator(function):
        def wrapper(self, *args):
            print("  {} {} : ".format(name, self.name), end="", flush=True)
            log = pj(self._log_dir, 'cmd_{}_{}.log'.format(name, self.name))
            context = Context(name, log)
            try:
                ret = function(self, *args, context=context)
                context._finalise()
                print("OK")
                return ret
            except SkipCommand:
                print("SKIP")
            except subprocess.CalledProcessError:
                print("ERROR")
                with open(log, 'r') as f:
                    print(f.read())
                raise StopBuild()
            except:
                print("ERROR")
                raise
        return wrapper
    return decorator


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
    def __init__(self, options):
        self.source_dir = pj(os.getcwd(), "SOURCE")
        self.build_dir = pj(os.getcwd(), "BUILD_{mode}".format(mode='native'))
        self.archive_dir = pj(os.getcwd(), "ARCHIVE")
        self.log_dir = pj(os.getcwd(), 'LOGS')
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        self.ninja_command = self._detect_ninja()
        self.meson_command = self._detect_meson()
        self.options = options
        self.libprefix = options.libprefix or self._detect_libdir()

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

    def run_command(self, command, cwd, context, env=None, input=None):
        os.makedirs(cwd, exist_ok=True)
        with open(context.log_file, 'w') as log:
            log.write("run command '{}'\n".format(command))
            if env:
                log.write("env is :\n")
                for k, v in env.items():
                    log.write("  {} : {!r}\n".format(k, v))
            log.flush()

            kwargs = dict()
            if env:
                kwargs['env'] = env
            if input:
                kwargs['stdin'] = input
            return subprocess.check_call(command, shell=True, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, **kwargs)

    def download(self, what, where=None):
        where = where or self.archive_dir
        file_path = pj(where, what.name)
        file_url = what.url or (REMOTE_PREFIX + what.name)
        if os.path.exists(file_path):
            if what.sha256 == get_sha256(file_path):
                raise SkipCommand()
            os.remove(file_path)
        urllib.request.urlretrieve(file_url, file_path)
        if what.sha256 != get_sha256(file_path):
            os.remove(file_path)
            raise StopBuild()


################################################################################
##### PROJECT
################################################################################
class Dependency:
    subsource_dir = None
    def __init__(self, buildEnv):
        self.buildEnv = buildEnv

    @property
    def source_path(self):
        if self.subsource_dir:
            return pj(self.buildEnv.source_dir, self.source_dir, self.subsource_dir)
        return pj(self.buildEnv.source_dir, self.source_dir)

    @property
    def build_path(self):
        return pj(self.buildEnv.build_dir, self.source_dir)

    @property
    def _log_dir(self):
        return self.buildEnv.log_dir


class ReleaseDownloadMixin:
    archive_top_dir = None
    @property
    def extract_path(self):
        return pj(self.buildEnv.source_dir, self.extract_dir)

    @property
    def source_dir(self):
        return "{}-{}".format(self.name, self.version)

    @property
    def extract_dir(self):
        return "{}-{}".format(self.name, self.version)

    @command("download")
    def _download(self, context):
        self.buildEnv.download(self.archive)

    @command("extract")
    def _extract(self, context):
        context.try_skip(self.extract_path)
        if os.path.exists(self.extract_path):
            shutil.rmtree(self.extract_path)
        extract_archive(pj(self.buildEnv.archive_dir, self.archive.name),
                           self.buildEnv.source_dir,
                           topdir=self.archive_top_dir,
                           name=self.extract_dir)

    @command("patch")
    def _patch(self, context):
        context.try_skip(self.extract_path)
        for p in self.patches:
            with open(pj(SCRIPT_DIR, 'patches', p), 'r') as patch_input:
                self.buildEnv.run_command("patch -p1", self.extract_path, context, input=patch_input)

    def prepare(self):
        self._download()
        self._extract()
        if hasattr(self, 'patches'):
            self._patch()


class GitCloneMixin:
    git_ref = "master"
    @property
    def source_dir(self):
        return self.git_dir

    @property
    def git_path(self):
        return pj(self.buildEnv.source_dir, self.git_dir)

    @command("gitclone")
    def _git_clone(self, context):
        if os.path.exists(self.git_path):
            raise SkipCommand()
        command = "git clone " + self.git_remote
        self.buildEnv.run_command(command, self.buildEnv.source_dir, context)

    @command("gitupdate")
    def _git_update(self, context):
        self.buildEnv.run_command("git pull", self.git_path, context)
        self.buildEnv.run_command("git checkout "+self.git_ref, self.git_path, context)

    def prepare(self):
        self._git_clone()
        self._git_update()


class MakeMixin:
    configure_option = ""
    make_option = ""
    install_option = ""
    configure_script = "configure"
    configure_env = None
    make_target = ""
    make_install_target = "install"

    @command("configure")
    def _configure(self, context):
        context.try_skip(self.build_path)
        command = "{configure_script} {configure_option} --prefix {install_dir} --libdir {libdir}"
        command = command.format(
            configure_script = pj(self.source_path, self.configure_script),
            configure_option = self.configure_option,
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

    @command("compile")
    def _compile(self, context):
        context.try_skip(self.build_path)
        command = "make -j4 {make_target} {make_option}".format(
            make_target = self.make_target,
            make_option = self.make_option
        )
        self.buildEnv.run_command(command, self.build_path, context)

    @command("install")
    def  _install(self, context):
        context.try_skip(self.build_path)
        command = "make {make_install_target} {make_option}".format(
            make_install_target = self.make_install_target,
            make_option = self.make_option
        )
        self.buildEnv.run_command(command, self.build_path, context)

    def build(self):
        self._configure()
        self._compile()
        self._install()


class CMakeMixin(MakeMixin):
    @command("configure")
    def _configure(self, context):
        context.try_skip(self.build_path)
        command = "cmake {configure_option} -DCMAKE_INSTALL_PREFIX={install_dir} -DCMAKE_INSTALL_LIBDIR={libdir} {source_path}"
        command = command.format(
            configure_option = self.configure_option,
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
        self.buildEnv.run_command(command, self.build_path, context, env=env)

class MesonMixin(MakeMixin):
    def _gen_env(self):
        env = Defaultdict(str, os.environ)
        env['PKG_CONFIG_PATH'] = (env['PKG_CONFIG_PATH'] + ':' + pj(self.buildEnv.install_dir, self.buildEnv.libprefix, 'pkgconfig')
                                  if env['PKG_CONFIG_PATH']
                                  else pj(self.buildEnv.install_dir, self.buildEnv.libprefix, 'pkgconfig')
                                 )
        env['PATH'] = ':'.join([pj(self.buildEnv.install_dir, 'bin'), env['PATH']])
        if self.buildEnv.build_static:
            env['LDFLAGS'] = env['LDFLAGS'] + " -static-libstdc++ --static"
        return env

    @command("configure")
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
        command = "{command} --default-library={library_type} {configure_option} . {build_path} --prefix={buildEnv.install_dir} --libdir={buildEnv.libprefix}".format(
            command = self.buildEnv.meson_command,
            library_type=library_type,
            configure_option=configure_option,
            build_path = self.build_path,
            buildEnv=self.buildEnv)
        self.buildEnv.run_command(command, self.source_path, context, env=env)

    @command("compile")
    def _compile(self, context):
        env = self._gen_env()
        command = "{} -v".format(self.buildEnv.ninja_command)
        self.buildEnv.run_command(command, self.build_path, context, env=env)

    @command("install")
    def _install(self, context):
        env = self._gen_env()
        command = "{} -v install".format(self.buildEnv.ninja_command)
        self.buildEnv.run_command(command, self.build_path, context)

    def build(self):
        self._configure()
        self._compile()
        self._install()


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

class UUID(Dependency, ReleaseDownloadMixin, MakeMixin):
    name = 'uuid'
    version = "1.42"
    archive = Remotefile('e2fsprogs-1.42.tar.gz',
                         '55b46db0cec3e2eb0e5de14494a88b01ff6c0500edf8ca8927cad6da7b5e4a46')
    source_dir = extract_dir = 'e2fsprogs-1.42'
    configure_option = "--enable-libuuid"
    configure_env = {'_format_CFLAGS' : "{env.CFLAGS} -fPIC"}
    make_target = 'libs'
    make_install_target = 'install-libs'


class Xapian(Dependency, ReleaseDownloadMixin, MakeMixin):
    name = "xapian-core"
    version = "1.4.0"
    archive = Remotefile('xapian-core-1.4.0.tar.xz',
                         '10584f57112aa5e9c0e8a89e251aecbf7c582097638bfee79c1fe39a8b6a6477')
    configure_option = "--enable-shared --enable-static --disable-sse --disable-backend-inmemory"
    patches = ["xapian_pkgconfig.patch"]
    configure_env = {'_format_LDFLAGS' : "-L{buildEnv.install_dir}/{buildEnv.libprefix}",
                     '_format_CXXFLAGS' : "-I{buildEnv.install_dir}/include"}


class CTPP2(Dependency, ReleaseDownloadMixin, CMakeMixin):
    name = "ctpp2"
    version = "2.8.3"
    archive = Remotefile('ctpp2-2.8.3.tar.gz',
                         'a83ffd07817adb575295ef40fbf759892512e5a63059c520f9062d9ab8fb42fc')
    configure_option = "-DMD5_SUPPORT=OFF"
    patches = ["ctpp2_include.patch", "ctpp2_no_src_modification.patch"]


class Pugixml(Dependency, ReleaseDownloadMixin, MesonMixin):
    name = "pugixml"
    version = "1.2"
    archive = Remotefile('pugixml-1.2.tar.gz',
                         '0f422dad86da0a2e56a37fb2a88376aae6e931f22cc8b956978460c9db06136b')
    patches = ["pugixml_meson.patch"]


class MicroHttpd(Dependency, ReleaseDownloadMixin, MakeMixin):
    name = "libmicrohttpd"
    version = "0.9.19"
    archive = Remotefile('libmicrohttpd-0.9.19.tar.gz',
                         'dc418c7a595196f09d2f573212a0d794404fa4ac5311fc9588c1e7ad7a90fae6')
    configure_option = "--enable-shared --enable-static --disable-https --without-libgcrypt --without-libcurl"


class Icu(Dependency, ReleaseDownloadMixin, MakeMixin):
    name = "icu4c"
    version = "56_1"
    archive = Remotefile('icu4c-56_1-src.tgz',
                         '3a64e9105c734dcf631c0b3ed60404531bce6c0f5a64bfe1a6402a4cc2314816'
                        )
    data = Remotefile('icudt56l.dat',
                      'e23d85eee008f335fc49e8ef37b1bc2b222db105476111e3d16f0007d371cbca')
    configure_option = "Linux --disable-samples --disable-tests --disable-extras --enable-static --disable-dyload"
    configure_script = "runConfigureICU"
    subsource_dir = "source"

    @command("download_data")
    def _download_data(self, context):
        self.buildEnv.download(self.data)

    @command("copy_data")
    def _copy_data(self, context):
        context.try_skip(self.source_path)
        shutil.copyfile(pj(self.buildEnv.archive_dir, self.data.name), pj(self.source_path, 'data', 'in', self.data.name))

    def prepare(self):
        super().prepare()
        self._download_data()
        self._copy_data()


class Zimlib(Dependency, GitCloneMixin, MesonMixin):
    name = "zimlib"
    #git_remote = "https://gerrit.wikimedia.org/r/p/openzim.git"
    git_remote = "https://github.com/mgautierfr/openzim"
    git_dir = "openzim"
    git_ref = "meson"
    subsource_dir = "zimlib"


class Kiwixlib(Dependency, GitCloneMixin, MesonMixin):
    name = "kiwix-lib"
    git_remote = "https://github.com/kiwix/kiwix-lib.git"
    git_dir = "kiwix-lib"
    configure_option = "-Dctpp2-install-prefix={buildEnv.install_dir}"


class KiwixTools(Dependency, GitCloneMixin, MesonMixin):
    name = "kiwix-tools"
    git_remote = "https://github.com/kiwix/kiwix-tools.git"
    git_dir = "kiwix-tools"
    configure_option = "-Dctpp2-install-prefix={buildEnv.install_dir}"


class Builder:
    def __init__(self, buildEnv):
        self.buildEnv = buildEnv
        self.dependencies = [UUID(buildEnv),
                             Xapian(buildEnv),
                             CTPP2(buildEnv),
                             Pugixml(buildEnv),
                             Zimlib(buildEnv),
                             MicroHttpd(buildEnv),
                             Icu(buildEnv),
                             Kiwixlib(buildEnv),
                             KiwixTools(buildEnv)
                            ]

    def prepare(self):
        for dependency in self.dependencies:
            print("prepare {} :".format(dependency.name))
            dependency.prepare()

    def build(self):
        for dependency in self.dependencies:
            print("build {} :".format(dependency.name))
            dependency.build()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('install_dir')
    parser.add_argument('--libprefix', default=None)
    parser.add_argument('--target_arch', default="x86_64")
    parser.add_argument('--build_static', action="store_true")
    return parser.parse_args()

if __name__ == "__main__":
    options = parse_args()
    options.install_dir = os.path.abspath(options.install_dir)
    buildEnv = BuildEnv(options)
    builder = Builder(buildEnv)
    try:
        print("[PREPARE]")
        builder.prepare()
        print("[BUILD]")
        builder.build()
    except StopBuild:
        print("Stopping build due to errors")
