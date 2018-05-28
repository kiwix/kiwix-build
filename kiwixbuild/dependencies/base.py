import subprocess
import os
import shutil

from kiwixbuild.utils import pj, Context, SkipCommand, extract_archive, Defaultdict, StopBuild
from kiwixbuild.versions import main_project_versions, base_deps_versions
from kiwixbuild._global import neutralEnv

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


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

    def __init__(self, buildEnv):
        self.buildEnv = buildEnv
        self.source = self.Source(self)
        self.builder = self.Builder(self)
        self.skip = False

    @property
    def version(self):
        return base_deps_versions.get(self.name, None)

    @property
    def full_name(self):
        if self.version:
            return "{}-{}".format(self.name, self.version)
        return self.name

    @property
    def source_path(self):
        return pj(neutralEnv('source_dir'), self.source.source_dir)

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
       inside the neutralEnv.source_dir."""
    def __init__(self, target):
        self.target = target

    @property
    def name(self):
        return self.target.name

    @property
    def source_dir(self):
        return self.target.full_name

    def _patch(self, context):
        source_path = pj(neutralEnv('source_dir'), self.source_dir)
        context.try_skip(source_path)
        context.force_native_build = True
        for p in self.patches:
            with open(pj(SCRIPT_DIR, 'patches', p), 'r') as patch_input:
                neutralEnv('run_command')("patch -p1", source_path, context, input=patch_input.read())

    def command(self, *args, **kwargs):
        return self.target.command(*args, **kwargs)


class NoopSource(Source):
    def prepare(self):
        pass


class ReleaseDownload(Source):
    archive_top_dir = None

    @property
    def extract_path(self):
        return pj(neutralEnv('source_dir'), self.source_dir)

    def _download(self, context):
        context.try_skip(neutralEnv('archive_dir'), self.name)
        neutralEnv('download')(self.archive)

    def _extract(self, context):
        context.try_skip(self.extract_path)
        if os.path.exists(self.extract_path):
            shutil.rmtree(self.extract_path)
        extract_archive(pj(neutralEnv('archive_dir'), self.archive.name),
                        neutralEnv('source_dir'),
                        topdir=self.archive_top_dir,
                        name=self.source_dir)

    def prepare(self):
        self.command('download', self._download)
        self.command('extract', self._extract)
        if hasattr(self, 'patches'):
            self.command('patch', self._patch)
        if hasattr(self, '_post_prepare_script'):
            self.command('post_prepare_script', self._post_prepare_script)


class GitClone(Source):
    base_git_ref = "master"

    @property
    def release_git_ref(self):
        return main_project_versions.get(self.name, "master")

    @property
    def source_dir(self):
        if neutralEnv('make_release'):
            return "{}_release".format(self.git_dir)
        else:
            return self.git_dir

    @property
    def git_path(self):
        return pj(neutralEnv('source_dir'), self.source_dir)

    @property
    def git_ref(self):
        if neutralEnv('make_release'):
            return self.release_git_ref
        else:
            return self.base_git_ref

    def _git_clone(self, context):
        if os.path.exists(self.git_path):
            raise SkipCommand()
        command = "git clone --depth=1 --branch {} {} {}".format(
            self.git_ref, self.git_remote, self.source_dir)
        neutralEnv('run_command')(command, neutralEnv('source_dir'), context)

    def _git_update(self, context):
        command = "git fetch origin {}".format(
            self.git_ref)
        neutralEnv('run_command')(command, self.git_path, context)
        neutralEnv('run_command')("git checkout "+self.git_ref, self.git_path, context)

    def prepare(self):
        self.command('gitclone', self._git_clone)
        self.command('gitupdate', self._git_update)
        if hasattr(self, '_post_prepare_script'):
            self.command('post_prepare_script', self._post_prepare_script)


class SvnClone(Source):
    @property
    def source_dir(self):
        return self.svn_dir

    @property
    def svn_path(self):
        return pj(neutralEnv('source_dir'), self.svn_dir)

    def _svn_checkout(self, context):
        if os.path.exists(self.svn_path):
            raise SkipCommand()
        command = "svn checkout {} {}".format(self.svn_remote, self.svn_dir)
        neutralEnv('run_command')(command, neutralEnv('source_dir'), context)

    def _svn_update(self, context):
        context.try_skip(self.svn_path)
        neutralEnv('run_command')("svn update", self.svn_path, context)

    def prepare(self):
        self.command('svncheckout', self._svn_checkout)
        self.command('svnupdate', self._svn_update)
        if hasattr(self, 'patches'):
            self.command('patch', self._patch)


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
        if hasattr(self, '_test'):
            self.command('test', self._test)
        self.command('install', self._install)
        if hasattr(self, '_post_build_script'):
            self.command('post_build_script', self._post_build_script)

    def make_dist(self):
        if hasattr(self, '_pre_build_script'):
            self.command('pre_build_script', self._pre_build_script)
        self.command('configure', self._configure)
        self.command('make_dist', self._make_dist)


class NoopBuilder(Builder):
    def build(self):
        pass

    def make_dist(self):
        pass


class MakeBuilder(Builder):
    configure_option_template = "{dep_options} {static_option} {env_option} --prefix {install_dir} --libdir {libdir}"
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
        option = self.configure_option_template.format(
            dep_options=self.configure_option,
            static_option=self.static_configure_option if self.buildEnv.platform_info.static else self.dynamic_configure_option,
            env_option=self.buildEnv.configure_option if not self.target.force_native_build else "",
            install_dir=self.buildEnv.install_dir,
            libdir=pj(self.buildEnv.install_dir, self.buildEnv.libprefix)
            )
        return option

    def _configure(self, context):
        context.try_skip(self.build_path)
        command = "{configure_script} {configure_option}"
        command = command.format(
            configure_script=pj(self.source_path, self.configure_script),
            configure_option=self.all_configure_option
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

    def _make_dist(self, context):
        context.try_skip(self.build_path)
        command = "make dist"
        self.buildEnv.run_command(command, self.build_path, context)


class CMakeBuilder(MakeBuilder):
    def _configure(self, context):
        context.try_skip(self.build_path)
        cross_option = ""
        if not self.target.force_native_build and self.buildEnv.cmake_crossfile:
            cross_option = "-DCMAKE_TOOLCHAIN_FILE={}".format(self.buildEnv.cmake_crossfile)
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
            cross_option=cross_option
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
        self.buildEnv.run_command(command, self.build_path, context, env=env, cross_env_only=True)


class MesonBuilder(Builder):
    configure_option = ""
    test_option = ""

    @property
    def library_type(self):
        return 'static' if self.buildEnv.platform_info.static else 'shared'

    def _configure(self, context):
        context.try_skip(self.build_path)
        if os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)
        os.makedirs(self.build_path)
        configure_option = self.configure_option.format(buildEnv=self.buildEnv)
        cross_option = ""
        if not self.target.force_native_build and self.buildEnv.meson_crossfile:
            cross_option = "--cross-file {}".format(
                self.buildEnv.meson_crossfile)
        command = ("{command} . {build_path}"
                   " --default-library={library_type}"
                   " {configure_option}"
                   " --prefix={buildEnv.install_dir}"
                   " --libdir={buildEnv.libprefix}"
                   " {cross_option}")
        command = command.format(
            command=neutralEnv('meson_command'),
            library_type=self.library_type,
            configure_option=configure_option,
            build_path=self.build_path,
            buildEnv=self.buildEnv,
            cross_option=cross_option
        )
        self.buildEnv.run_command(command, self.source_path, context, cross_env_only=True)

    def _compile(self, context):
        command = "{} -v".format(neutralEnv('ninja_command'))
        self.buildEnv.run_command(command, self.build_path, context)

    def _test(self, context):
        if ( self.buildEnv.platform_info.build == 'android'
             or (self.buildEnv.platform_info.build != 'native'
                 and not self.buildEnv.platform_info.static)
           ):
            raise SkipCommand()
        command = "{} --verbose {}".format(neutralEnv('mesontest_command'), self.test_option)
        self.buildEnv.run_command(command, self.build_path, context)

    def _install(self, context):
        command = "{} -v install".format(neutralEnv('ninja_command'))
        self.buildEnv.run_command(command, self.build_path, context)

    def _make_dist(self, context):
        command = "{} -v dist".format(neutralEnv('ninja_command'))
        self.buildEnv.run_command(command, self.build_path, context)


class GradleBuilder(Builder):
    gradle_target = "build"
    gradle_option = "-i"

    def build(self):
        self.command('configure', self._configure)
        if hasattr(self, '_pre_compile_script'):
            self.command('pre_compile_script', self._pre_compile_script)
        self.command('compile', self._compile)

    def _configure(self, context):
        # We don't have a lot to configure by itself
        context.try_skip(self.build_path)
        if os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)
        shutil.copytree(self.source_path, self.build_path)

    def _compile(self, context):
        command = "gradle {gradle_target} {gradle_option}"
        command = command.format(
            gradle_target=self.gradle_target,
            gradle_option=self.gradle_option)
        self.buildEnv.run_command(command, self.build_path, context)
