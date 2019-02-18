import subprocess
import os
import shutil

from kiwixbuild.utils import pj, Context, SkipCommand, extract_archive, Defaultdict, StopBuild, run_command
from kiwixbuild.versions import main_project_versions, base_deps_versions
from kiwixbuild._global import neutralEnv, option

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
    force_native_build = False

    @classmethod
    def version(cls):
        if cls.name in base_deps_versions:
            return base_deps_versions[cls.name]
        elif option('make_release'):
            return main_project_versions.get(cls.name, None)
        return None

    @classmethod
    def full_name(cls):
        if cls.version():
            return "{}-{}".format(cls.name, cls.version())
        return cls.name


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
        return self.target.full_name()

    @property
    def source_path(self):
        return pj(neutralEnv('source_dir'), self.source_dir)

    @property
    def _log_dir(self):
        return neutralEnv('log_dir')

    def _patch(self, context):
        context.try_skip(self.source_path)
        context.force_native_build = True
        for p in self.patches:
            with open(pj(SCRIPT_DIR, 'patches', p), 'r') as patch_input:
                run_command("patch -p1", self.source_path, context, input=patch_input.read())

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
        if option('make_release'):
            return "{}_release".format(self.git_dir)
        else:
            return self.git_dir

    @property
    def git_path(self):
        return pj(neutralEnv('source_dir'), self.source_dir)

    @property
    def git_ref(self):
        if option('make_release'):
            return self.release_git_ref
        else:
            return self.base_git_ref

    def _git_clone(self, context):
        if os.path.exists(self.git_path):
            raise SkipCommand()
        command = "git clone --depth=1 --branch {} {} {}".format(
            self.git_ref, self.git_remote, self.source_dir)
        run_command(command, neutralEnv('source_dir'), context)

    def _git_update(self, context):
        command = "git fetch origin {}".format(
            self.git_ref)
        run_command(command, self.git_path, context)
        run_command("git checkout "+self.git_ref, self.git_path, context)

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

    def _svn_export(self, context):
        if os.path.exists(self.svn_path):
            raise SkipCommand()
        command = "svn export {} {}".format(self.svn_remote, self.svn_dir)
        run_command(command, neutralEnv('source_dir'), context)

    def prepare(self):
        self.command('svnexport', self._svn_export)
        if hasattr(self, 'patches'):
            self.command('patch', self._patch)


class Builder:
    subsource_dir = None
    dependencies = []

    def __init__(self, target, source, buildEnv):
        self.target = target
        self.source = source
        self.buildEnv = buildEnv

    @classmethod
    def get_dependencies(cls, platformInfo, allDeps):
        return cls.dependencies

    @property
    def name(self):
        return self.target.name

    @property
    def source_path(self):
        base_source_path = self.source.source_path
        if self.subsource_dir:
            return pj(base_source_path, self.subsource_dir)
        return base_source_path

    @property
    def build_path(self):
        return pj(self.buildEnv.build_dir, self.target.full_name())

    @property
    def _log_dir(self):
        return self.buildEnv.log_dir

    def command(self, name, function, *args):
        print("  {} {} : ".format(name, self.name), end="", flush=True)
        log = pj(self._log_dir, 'cmd_{}_{}.log'.format(name, self.name))
        context = Context(name, log, self.target.force_native_build)
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

    def set_flatpak_buildsystem(self, module):
        if getattr(self, 'flatpak_buildsystem', None):
            module['buildsystem'] = self.flatpak_buildsystem
        if getattr(self, 'configure_option', ''):
            module['config-opts'] = self.configure_option.split(' ')


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
    flatpak_buildsystem = None

    @property
    def make_install_target(self):
        if self.buildEnv.platformInfo.build == 'iOS':
            return 'install'
        return 'install-strip'

    @property
    def all_configure_option(self):
        option = self.configure_option_template.format(
            dep_options=self.configure_option,
            static_option=self.static_configure_option if self.buildEnv.platformInfo.static else self.dynamic_configure_option,
            env_option=self.buildEnv.platformInfo.configure_option if not self.target.force_native_build else "",
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
        if self.buildEnv.platformInfo.static:
            env['CFLAGS'] = env['CFLAGS'] + ' -fPIC'
            env['CXXFLAGS'] = env['CXXFLAGS'] + ' -fPIC'
        if self.configure_env:
            for k in self.configure_env:
                if k.startswith('_format_'):
                    v = self.configure_env.pop(k)
                    v = v.format(buildEnv=self.buildEnv, env=env)
                    self.configure_env[k[8:]] = v
            env.update(self.configure_env)
        run_command(command, self.build_path, context, buildEnv=self.buildEnv, env=env)

    def _compile(self, context):
        context.try_skip(self.build_path)
        command = "make -j4 {make_target} {make_option}".format(
            make_target=self.make_target,
            make_option=self.make_option
        )
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)

    def _install(self, context):
        context.try_skip(self.build_path)
        command = "make {make_install_target} {make_option}".format(
            make_install_target=self.make_install_target,
            make_option=self.make_option
        )
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)

    def _make_dist(self, context):
        context.try_skip(self.build_path)
        command = "make dist"
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)


class CMakeBuilder(MakeBuilder):
    flatpak_buildsystem = 'cmake'

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
            configure_option=self.configure_option,
            install_dir=self.buildEnv.install_dir,
            libdir=self.buildEnv.libprefix,
            source_path=self.source_path,
            cross_option=cross_option
        )
        env = Defaultdict(str, os.environ)
        if self.buildEnv.platformInfo.static:
            env['CFLAGS'] = env['CFLAGS'] + ' -fPIC'
            env['CXXFLAGS'] = env['CXXFLAGS'] + ' -fPIC'
        if self.configure_env:
            for k in self.configure_env:
                if k.startswith('_format_'):
                    v = self.configure_env.pop(k)
                    v = v.format(buildEnv=self.buildEnv, env=env)
                    self.configure_env[k[8:]] = v
            env.update(self.configure_env)
        run_command(command, self.build_path, context, env=env, buildEnv=self.buildEnv, cross_env_only=True)

    def set_flatpak_buildsystem(self, module):
        super().set_flatpak_buildsystem( module)
        module['buildir'] = True


class QMakeBuilder(MakeBuilder):
    qmake_target = ""
    flatpak_buildsystem = 'qmake'

    @property
    def env_option(self):
        options = ""
        if 'QMAKE_CC' in os.environ:
            options += 'QMAKE_CC={} '.format(os.environ['QMAKE_CC'])
        if 'QMAKE_CXX' in os.environ:
            options += 'QMAKE_CXX={} '.format(os.environ['QMAKE_CXX'])
        return options

    def _configure(self, context):
        context.try_skip(self.build_path)
        cross_option = ""
        command = ("qmake {configure_option}"
                   " {env_option}"
                   " {source_path}"
                   " {cross_option}")
        command = command.format(
            configure_option=self.configure_option,
            env_option=self.env_option,
            source_path=self.source_path,
            cross_option=cross_option
        )
        run_command(command, self.build_path, context, buildEnv=self.buildEnv, cross_env_only=True)

    def _install(self, context):
        context.try_skip(self.build_path)
        command = "make {make_install_target} {make_option}".format(
            make_install_target=self.make_install_target,
            make_option=self.make_option
        )
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)

    def _make_dist(self, context):
        command = "git archive -o {build_dir}/{name}.tar.gz --prefix={name}/ HEAD"
        command = command.format(
            build_dir = self.build_path,
            name = self.target.full_name()
        )
        run_command(command, self.source_path, context, buildEnv=self.buildEnv)



class MesonBuilder(Builder):
    configure_option = ""
    test_option = ""
    flatpak_buildsystem = 'meson'

    @property
    def build_type(self):
        return 'release' if option('make_release') else 'debugoptimized'

    @property
    def strip_option(self):
        return '--strip' if option('make_release') else ''

    @property
    def library_type(self):
        return 'static' if self.buildEnv.platformInfo.static else 'shared'

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
                   " --buildtype={build_type} {strip_option}"
                   " --default-library={library_type}"
                   " {configure_option}"
                   " --prefix={buildEnv.install_dir}"
                   " --libdir={buildEnv.libprefix}"
                   " {cross_option}")
        command = command.format(
            command=neutralEnv('meson_command'),
            build_type=self.build_type,
            strip_option=self.strip_option,
            library_type=self.library_type,
            configure_option=configure_option,
            build_path=self.build_path,
            buildEnv=self.buildEnv,
            cross_option=cross_option
        )
        run_command(command, self.source_path, context, buildEnv=self.buildEnv, cross_env_only=True)

    def _compile(self, context):
        command = "{} -v".format(neutralEnv('ninja_command'))
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)

    def _test(self, context):
        if ( self.buildEnv.platformInfo.build == 'android'
             or (self.buildEnv.platformInfo.build != 'native'
                 and not self.buildEnv.platformInfo.static)
           ):
            raise SkipCommand()
        command = "{} --verbose {}".format(neutralEnv('mesontest_command'), self.test_option)
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)

    def _install(self, context):
        command = "{} -v install".format(neutralEnv('ninja_command'))
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)

    def _make_dist(self, context):
        command = "{} -v dist".format(neutralEnv('ninja_command'))
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)


class GradleBuilder(Builder):
    gradle_target = "assembleKiwixRelease assembleKiwixDebug"
    gradle_option = "-i --no-daemon --build-cache"

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
        run_command(command, self.build_path, context, buildEnv=self.buildEnv)
