import subprocess
import os
import shutil
import time

from kiwixbuild.utils import pj, Context, SkipCommand, WarningMessage, extract_archive, StopBuild, run_command, colorize, copy_tree
from kiwixbuild.versions import main_project_versions, base_deps_versions
from kiwixbuild._global import neutralEnv, option, get_target_step

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
    force_build = False
    force_native_build = False
    dont_skip = False

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
    def full_name(self):
        return self.target.full_name()

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
        for p in self.patches:
            patch_file_path = pj(SCRIPT_DIR, 'patches', p)
            patch_command = "patch -p1 -i {patch}".format(patch=patch_file_path)
            run_command(patch_command, self.source_path, context)

    def command(self, name, function, *args):
        print("  {} {} : ".format(name, self.name), end="", flush=True)
        log = pj(self._log_dir, 'cmd_{}_{}.log'.format(name, self.name))
        context = Context(name, log, True)
        try:
            start_time = time.time()
            ret = function(*args, context=context)
            context._finalise()
            duration = time.time() - start_time
            print(colorize("OK"), "({:.1f}s)".format(duration))
            return ret
        except WarningMessage as e:
            print(e)
        except SkipCommand as e:
            print(e)
        except subprocess.CalledProcessError:
            print(colorize("ERROR"))
            try:
                with open(log, 'r') as f:
                    print(f.read())
            except:
                pass
            raise StopBuild()
        except:
            print(colorize("ERROR"))
            raise


class NoopSource(Source):
    def prepare(self):
        pass


class ReleaseDownload(Source):
    archive_top_dir = None

    @property
    def archives(self):
        return (self.archive, )

    @property
    def extract_path(self):
        return pj(neutralEnv('source_dir'), self.source_dir)

    def _download(self, context):
        context.try_skip(neutralEnv('archive_dir'), self.full_name)
        for archive in self.archives:
            neutralEnv('download')(archive)

    def _extract(self, context):
        context.try_skip(self.extract_path)
        if os.path.exists(self.extract_path):
            shutil.rmtree(self.extract_path)
        for archive in self.archives:
            extract_archive(pj(neutralEnv('archive_dir'), archive.name),
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
    base_git_ref = "main"
    force_full_clone = False

    @property
    def release_git_ref(self):
        return main_project_versions.get(self.name, self.base_git_ref)

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

    def _git_init(self, context):
        if option('fast_clone') and self.force_full_clone == False:
            command = "git clone --depth=1 --branch {} {} {}".format(
                self.git_ref, self.git_remote, self.source_dir)
            run_command(command, neutralEnv('source_dir'), context)
        else:
            command = "git clone {} {}".format(self.git_remote, self.source_dir)
            run_command(command, neutralEnv('source_dir'), context)
            command = "git checkout {}".format(self.git_ref)
            run_command(command, self.git_path, context)

    def _git_update(self, context):
        command = "git fetch origin {}".format(self.git_ref)
        run_command(command, self.git_path, context)
        try:
            command = "git merge --ff-only origin/{}".format(self.git_ref)
            run_command(command, self.git_path, context)
        except subprocess.CalledProcessError:
            raise WarningMessage("Cannot update, please check log for information")

    def prepare(self):
        if not os.path.exists(self.git_path):
            self.command('gitinit', self._git_init)
        else:
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
        if self.target.force_build:
            context.no_skip = True
        try:
            start_time = time.time()
            ret = function(*args, context=context)
            context._finalise()
            duration = time.time() - start_time
            print(colorize("OK"), "({:.1f}s)".format(duration))
            return ret
        except SkipCommand as e:
            print(e)
        except WarningMessage as e:
            print(e)
        except subprocess.CalledProcessError:
            print(colorize("ERROR"))
            try:
                with open(log, 'r') as f:
                    print(f.read())
            except:
                pass
            raise StopBuild()
        except:
            print(colorize("ERROR"))
            raise

    def build(self):
        if hasattr(self, '_pre_build_script'):
            self.command('pre_build_script', self._pre_build_script)
        self.command('configure', self._configure)
        if hasattr(self, '_post_configure_script'):
            self.command('post_configure_script', self._post_configure_script)
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
        if getattr(self, 'subsource_dir', None):
            module['subdir'] = self.subsource_dir
        if getattr(self, 'flatpack_build_options', None):
            module['build-options'] = self.flatpack_build_options
        if getattr(self, 'configure_option', ''):
            module['config-opts'] = self.configure_option.split(' ')

    def get_env(self, *, cross_comp_flags, cross_compilers, cross_path):
        env = self.buildEnv.get_env(cross_comp_flags=cross_comp_flags, cross_compilers=cross_compilers, cross_path=cross_path)
        for dep in self.get_dependencies(self.buildEnv.platformInfo, False):
            try:
                builder = get_target_step(dep, self.buildEnv.platformInfo.name)
                builder.set_env(env)
            except KeyError:
                # Some target may be missing (installed by a package, ...)
                pass
        return env

    def set_env(self, env):
        pass


class NoopBuilder(Builder):
    def build(self):
        pass

    def make_dist(self):
        pass


class TcCopyBuilder(Builder):
    src_subdir = None

    @property
    def build_path(self):
        return pj(self.buildEnv.toolchain_dir, self.target.full_name())

    def build(self):
        self.command('copy', self._copy)

    def _copy(self, context):
        context.try_skip(self.build_path)
        if self.src_subdir:
            source_path = pj(self.source_path, self.src_subdir)
        else:
            source_path = self.source_path
        copy_tree(source_path, self.build_path)

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
    configure_env = {
        '_format_CFLAGS' : '{env[CFLAGS]} -O3',
        '_format_CXXFLAGS': '{env[CXXFLAGS]} -O3'
    }
    make_target = ""
    flatpak_buildsystem = None

    @property
    def make_install_target(self):
        if self.buildEnv.platformInfo.build in ('iOS', "wasm"):
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

    def set_configure_env(self, env):
        dep_conf_env = self.configure_env
        if not dep_conf_env:
            return
        for k, v in dep_conf_env.items():
            if k.startswith('_format_'):
                v = v.format(buildEnv=self.buildEnv, env=env)
                env[k[8:]] = v
            else:
                env[k] = v


    def _configure(self, context):
        context.try_skip(self.build_path)
        command = "{configure_wrapper}{configure_script} {configure_option}"
        command = command.format(
            configure_wrapper=self.buildEnv.configure_wrapper,
            configure_script=pj(self.source_path, self.configure_script),
            configure_option=self.all_configure_option
        )
        env = self.get_env(cross_comp_flags=True, cross_compilers=True, cross_path=True)
        self.set_configure_env(env)
        run_command(command, self.build_path, context, env=env)

    def _compile(self, context):
        context.try_skip(self.build_path)
        command = "{make_wrapper}make -j4 {make_target} {make_option}".format(
            make_wrapper=self.buildEnv.make_wrapper,
            make_target=self.make_target,
            make_option=self.make_option
        )
        env = self.get_env(cross_comp_flags=True, cross_compilers=True, cross_path=True)
        run_command(command, self.build_path, context, env=env)

    def _install(self, context):
        context.try_skip(self.build_path)
        command = "{make_wrapper}make {make_install_target} {make_option}".format(
            make_wrapper=self.buildEnv.make_wrapper,
            make_install_target=self.make_install_target,
            make_option=self.make_option
        )
        env = self.get_env(cross_comp_flags=True, cross_compilers=True, cross_path=True)
        run_command(command, self.build_path, context, env=env)

    def _make_dist(self, context):
        context.try_skip(self.build_path)
        command = "{make_wrapper}make dist".format(
            make_wrapper=self.buildEnv.make_wrapper
        )
        env = self.get_env(cross_comp_flags=True, cross_compilers=True, cross_path=True)
        run_command(command, self.build_path, context, env=env)


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
        env = self.get_env(cross_comp_flags=True, cross_compilers=False, cross_path=True)
        self.set_configure_env(env)
        run_command(command, self.build_path, context, env=env)

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
        command = ("{command} {configure_option}"
                   " {env_option}"
                   " {source_path}"
                   " {cross_option}")
        command = command.format(
            command = neutralEnv('qmake_command'),
            configure_option=self.configure_option,
            env_option=self.env_option,
            source_path=self.source_path,
            cross_option=cross_option
        )
        env = self.get_env(cross_comp_flags=True, cross_compilers=False, cross_path=True)
        self.set_configure_env(env)
        run_command(command, self.build_path, context, env=env)

    def _make_dist(self, context):
        command = "git archive -o {build_dir}/{name}.tar.gz --prefix={name}/ HEAD"
        command = command.format(
            build_dir = self.build_path,
            name = self.target.full_name()
        )
        run_command(command, self.source_path, context)



class MesonBuilder(Builder):
    configure_option = ""
    test_option = ""
    flatpak_buildsystem = 'meson'

    @property
    def build_type(self):
        return 'release' if option('make_release') else 'debug'

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
        env = self.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=True)
        run_command(command, self.source_path, context, env=env)

    def _compile(self, context):
        context.try_skip(self.build_path)
        command = "{} -v".format(neutralEnv('ninja_command'))
        env = self.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=True)
        run_command(command, self.build_path, context, env=env)

    def _test(self, context):
        context.try_skip(self.build_path)
        if ( self.buildEnv.platformInfo.build == 'android'
             or (self.buildEnv.platformInfo.build != 'native'
                 and not self.buildEnv.platformInfo.static)
           ):
            raise SkipCommand()
        command = "{} --verbose {}".format(neutralEnv('mesontest_command'), self.test_option)
        env = self.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=True)
        run_command(command, self.build_path, context, env=env)

    def _install(self, context):
        context.try_skip(self.build_path)
        command = "{} -v install".format(neutralEnv('ninja_command'))
        env = self.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=True)
        run_command(command, self.build_path, context, env=env)

    def _make_dist(self, context):
        command = "{} -v dist".format(neutralEnv('ninja_command'))
        env = self.get_env(cross_comp_flags=False, cross_compilers=False, cross_path=True)
        run_command(command, self.build_path, context, env=env)
