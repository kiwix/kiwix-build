import subprocess
import os
import shutil

from utils import pj, Context, SkipCommand, extract_archive, Defaultdict, StopBuild

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


class _MetaDependency(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name != 'Dependency':
            dep_name = dct['name']
            Dependency.all_deps[dep_name] = _class
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
        context = Context(name, log, self.force_native_build)
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
        context.force_native_build = True
        for p in self.patches:
            with open(pj(SCRIPT_DIR, 'patches', p), 'r') as patch_input:
                self.buildEnv.run_command("patch -p1", self.extract_path, context, input=patch_input)

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
        context.force_native_build = True
        if os.path.exists(self.git_path):
            raise SkipCommand()
        command = "git clone " + self.git_remote
        self.buildEnv.run_command(command, self.buildEnv.source_dir, context)

    def _git_update(self, context):
        context.force_native_build = True
        self.buildEnv.run_command("git fetch", self.git_path, context)
        self.buildEnv.run_command("git checkout "+self.git_ref, self.git_path, context)

    def prepare(self):
        self.command('gitclone', self._git_clone)
        self.command('gitupdate', self._git_update)
        if hasattr(self, '_post_prepare_script'):
            self.command('post_prepare_script', self._post_prepare_script)


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
        if hasattr(self, '_pre_build_script'):
            self.command('pre_build_script', self._pre_build_script)
        self.command('configure', self._configure)
        self.command('compile', self._compile)
        self.command('install', self._install)
        if hasattr(self, '_post_build_script'):
            self.command('post_build_script', self._post_build_script)


class MakeBuilder(Builder):
    configure_option = ""
    dynamic_configure_option = "--enable-shared --disable-static"
    static_configure_option = "--enable-static --disable-shared"
    make_option = ""
    install_option = ""
    configure_script = "configure"
    configure_env = None
    make_target = ""
    make_install_target = "install"

    @property
    def all_configure_option(self):
        return "{} {} {}".format(
            self.configure_option,
            self.static_configure_option if self.buildEnv.platform_info.static else self.dynamic_configure_option,
            self.buildEnv.configure_option if not self.target.force_native_build else "")

    def _configure(self, context):
        context.try_skip(self.build_path)
        command = "{configure_script} {configure_option} --prefix {install_dir} --libdir {libdir}"
        command = command.format(
            configure_script=pj(self.source_path, self.configure_script),
            configure_option=self.all_configure_option,
            install_dir=self.buildEnv.install_dir,
            libdir=pj(self.buildEnv.install_dir, self.buildEnv.libprefix)
        )
        env = Defaultdict(str, os.environ)
        if self.buildEnv.platform_info.static:
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
            make_target=self.make_target,
            make_option=self.make_option
        )
        self.buildEnv.run_command(command, self.build_path, context)

    def _install(self, context):
        context.try_skip(self.build_path)
        command = "make {make_install_target} {make_option}".format(
            make_install_target=self.make_install_target,
            make_option=self.make_option
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
            configure_option="{} {}".format(self.buildEnv.cmake_option, self.configure_option),
            install_dir=self.buildEnv.install_dir,
            libdir=self.buildEnv.libprefix,
            source_path=self.source_path,
            cross_option="-DCMAKE_TOOLCHAIN_FILE={}".format(self.buildEnv.cmake_crossfile) if self.buildEnv.cmake_crossfile else ""
        )
        env = Defaultdict(str, os.environ)
        if self.buildEnv.platform_info.static:
            env['CFLAGS'] = env['CFLAGS'] + ' -fPIC'
        if self.configure_env:
            for k in self.configure_env:
                if k.startswith('_format_'):
                    v = self.configure_env.pop(k)
                    v = v.format(buildEnv=self.buildEnv, env=env)
                    self.configure_env[k[8:]] = v
            env.update(self.configure_env)
        self.buildEnv.run_command(command, self.build_path, context, env=env, cross_path_only=True)


class MesonBuilder(Builder):
    configure_option = ""

    @property
    def library_type(self):
        return 'static' if self.buildEnv.platform_info.static else 'shared'

    def _configure(self, context):
        context.try_skip(self.build_path)
        if os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)
        os.makedirs(self.build_path)
        configure_option = self.configure_option.format(buildEnv=self.buildEnv)
        command = ("{command} . {build_path}"
                   " --default-library={library_type}"
                   " {configure_option}"
                   " --prefix={buildEnv.install_dir}"
                   " --libdir={buildEnv.libprefix}"
                   " {cross_option}")
        command = command.format(
            command=self.buildEnv.meson_command,
            library_type=self.library_type,
            configure_option=configure_option,
            build_path=self.build_path,
            buildEnv=self.buildEnv,
            cross_option="--cross-file {}".format(self.buildEnv.meson_crossfile) if self.buildEnv.meson_crossfile else ""
        )
        self.buildEnv.run_command(command, self.source_path, context, cross_path_only=True)

    def _compile(self, context):
        command = "{} -v".format(self.buildEnv.ninja_command)
        self.buildEnv.run_command(command, self.build_path, context)

    def _install(self, context):
        command = "{} -v install".format(self.buildEnv.ninja_command)
        self.buildEnv.run_command(command, self.build_path, context)
