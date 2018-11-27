
import sys
from collections import OrderedDict
from .buildenv import *

from .platforms import PlatformInfo
from .utils import remove_duplicates, run_command, StopBuild, Context
from .dependencies import Dependency
from .packages import PACKAGE_NAME_MAPPERS
from ._global import (
    neutralEnv, option,
    add_target_step, get_target_step, target_steps,
    backend)
from . import _global
from .dependencies.base import (
    Source,
    Builder,
    ReleaseDownload,
    GitClone,
    MesonBuilder,
    CMakeBuilder,
    QMakeBuilder,
    MakeBuilder,
    SCRIPT_DIR)
import json
from shutil import copyfile

MANIFEST = {
    'app-id': 'org.kiwix.Client',
    'runtime': 'org.kde.Platform',
    'runtime-version': '5.11',
    'sdk': 'org.kde.Sdk',
    'command': 'kiwix-desktop',
    'rename-desktop-file' : 'kiwix-desktop.desktop',
    'rename-icon': 'kiwix-desktop',
    'finish-args': [
        '--socket=wayland',
        '--socket=x11',
        '--share=network',
        '--share=ipc',
        '--device=dri',
        '--socket=pulseaudio',
        '--filesystem=xdg-data',
    ],
    'cleanup': [
        '/include',
        '/lib/pkgconfig',
        '/lib/cmake',
        '/lib/*.la',
        '/bin/curl',
        '/bin/copydatabase',
        '/bin/kiwix-compile-resources',
        '/bin/quest',
        '/bin/simple*',
        '/bin/xapian-*',
        '/share/aclocal',
        '/share/doc',
        '/share/man'
    ]
}



class FlatpakBuilder:
    def __init__(self):
        self._targets = {}
        PlatformInfo.get_platform('neutral', self._targets)
        self.platform = PlatformInfo.get_platform('flatpak', self._targets)
        if neutralEnv('distname') not in self.platform.compatible_hosts:
            print(('ERROR: The target platform {} cannot be build on host {}.\n'
                   'Select another target platform or change your host system.'
                  ).format(self.platform.name, neutralEnv('distname')))
        self.targetDefs = self.platform.add_targets(option('target'), self._targets)

    def finalize_target_steps(self):
        steps = []
        for targetDef in self.targetDefs:
            steps += self.order_steps(targetDef)
        steps = list(remove_duplicates(steps))

        for pltName in PlatformInfo.all_running_platforms:
            plt = PlatformInfo.all_platforms[pltName]
            for tlcName in plt.toolchain_names:
                tlc = Dependency.all_deps[tlcName]
                src_plt_step = ('source', tlcName)
                add_target_step(src_plt_step, self._targets[src_plt_step])
                blt_plt_step = ('neutral' if tlc.neutral else pltName, tlcName)
                add_target_step(blt_plt_step, self._targets[blt_plt_step])

        for dep in steps:
            add_target_step(dep, self._targets[dep])
        self.instanciate_steps()

    def order_steps(self, targetDef):
        _targets = dict(self._targets)
        yield from self.order_dependencies(targetDef, _targets)

    def order_dependencies(self, targetDef, targets):
        targetPlatformName, targetName = targetDef
        if targetPlatformName == 'source':
            # Do not try to order sources, they will be added as dep by the
            # build step two lines later.
            return
        try:
            target = targets.pop(targetDef)
        except KeyError:
            return

        targetPlatform = PlatformInfo.get_platform(targetPlatformName)
        for dep in target.get_dependencies(targetPlatform, True):
            if isinstance(dep, tuple):
                depPlatform, depName = dep
            else:
                depPlatform, depName = targetPlatformName, dep
            if (depPlatform, depName) in targets:
                yield from self.order_dependencies((depPlatform, depName), targets)
        yield ('source', targetName)
        yield targetDef

    def instanciate_steps(self):
        for stepDef in list(target_steps()):
            stepPlatform, stepName = stepDef
            stepClass = Dependency.all_deps[stepName]
            if stepPlatform == 'source':
                source = get_target_step(stepDef)(stepClass)
                add_target_step(stepDef, source)
            else:
                source = get_target_step(stepName, 'source')
                env = PlatformInfo.get_platform(stepPlatform).buildEnv
                builder = get_target_step(stepDef)(stepClass, source, env)
                add_target_step(stepDef, builder)

    def configure(self):
        steps = remove_duplicates(target_steps())
        modules = {}
        for stepDef in steps:
            module = modules.setdefault(stepDef[1], {})
            module['name'] = stepDef[1]
            if stepDef[0] == 'source':
                source = get_target_step(stepDef)
                module['no-autogen'] = getattr(source, 'flatpack_no_autogen', False)
                module_sources = module.setdefault('sources', [])
                if isinstance(source, ReleaseDownload):
                    src = {
                        'type': 'archive',
                        'sha256': source.archive.sha256,
                        'url': source.archive.url
                    }
                    if hasattr(source, 'flatpak_dest'):
                        src['dest'] = source.flatpak_dest
                    module_sources.append(src)
                elif isinstance(source, GitClone):
                    src = {
                        'type': 'git',
                        'url': source.git_remote,
                        'tag': source.git_ref
                    }
                    module_sources.append(src)
                for p in getattr(source, 'patches', []):
                    patch = {
                        'type': 'patch',
                        'path': 'patches/' + p
                    }
                    module_sources.append(patch)

                if hasattr(source, 'flatpak_command'):
                    command = {
                        'type': 'shell',
                        'commands': [source.flatpak_command]
                    }
                    module_sources.append(command)

            else:
                builder = get_target_step(stepDef)
                if isinstance(builder, MesonBuilder):
                    module['buildsystem'] = 'meson'
                    module['builddir'] = True
                elif isinstance(builder, CMakeBuilder):
                    module['buildsystem'] = 'cmake'
                    module['builddir'] = True
                elif isinstance(builder, QMakeBuilder):
                    module['buildsystem'] = 'qmake'
                # config-opts
                print(builder)
                if getattr(builder, 'configure_option', ''):
                    module['config-opts'] = builder.configure_option.split(' ')

        manifest = MANIFEST.copy()
        manifest['modules'] = list(modules.values())
        with open(pj(self.platform.buildEnv.build_dir, 'manifest.json'), 'w') as f:
            f.write(json.dumps(manifest, indent=4))

    def copy_patches(self):
        sourceDefs = (tDef for tDef in target_steps() if tDef[0] == 'source')
        for sourceDef in sourceDefs:
            source = get_target_step(sourceDef)
            if not hasattr(source, 'patches'):
                continue
            for p in source.patches:
                path = pj(SCRIPT_DIR, 'patches', p)
                os.makedirs(pj(self.platform.buildEnv.build_dir, 'patches'), exist_ok=True)
                dest = pj(self.platform.buildEnv.build_dir, 'patches', p)
                copyfile(path, dest)


    def build(self):
        log = pj(self.platform.buildEnv.log_dir, 'cmd_build_flatpak.log')
        context = Context('build', log, False)
        command = "flatpak-builder --user --ccache --force-clean --repo=repo builddir manifest.json"
        try:
            run_command(command, self.platform.buildEnv.build_dir, context, self.platform.buildEnv)
            context._finalise()
        except subprocess.CalledProcessError:
            try:
                with open(log, 'r') as f:
                    print(f.read())
            except:
                pass

    def bundle(self):
        log = pj(self.platform.buildEnv.log_dir, 'cmd_bundle_flatpak.log')
        context = Context('bundle', log, False)
        command = "flatpak build-bundle repo {id}.flatpak {id}"
        command = command.format(id = MANIFEST['app-id'])
        try:
            run_command(command, self.platform.buildEnv.build_dir, context, self.platform.buildEnv)
            context._finalise()
        except subprocess.CalledProcessError:
            try:
                with open(log, 'r') as f:
                    print(f.read())
            except:
                pass


    def _get_packages(self):
        package_name_mapper = PACKAGE_NAME_MAPPERS.get('flatpak', {})

        to_drop = []
        for builderDef in self._targets:
            platformName, builderName = builderDef
            packages = package_name_mapper.get(builderName)
            if packages:
                to_drop.append(builderDef)
        for dep in to_drop:
            del self._targets[dep]

    def run(self):
        try:
            # This is a small hack, we don't need the list of packages to
            # install in a flatpak sdk, but _get_packages() will drop the
            # dependencies we already have in the sdk.
            self._get_packages()
            self.finalize_target_steps()
            print("[SETUP PLATFORMS]")
            for platform in PlatformInfo.all_running_platforms.values():
                platform.finalize_setup()
            for pltName in PlatformInfo.all_running_platforms:
                plt = PlatformInfo.all_platforms[pltName]
                for tlcName in plt.toolchain_names:
                    tlc = Dependency.all_deps[tlcName]
                    builderDef = (pltName, tlcName)
                    builder = get_target_step(builderDef)
                    print("build {} ({}):".format(builder.name, pltName[0]))
                    add_target_step(builderDef, builder)
                    builder.build()
            print("[GENERATE FLATPAK MANIFEST]")
            self.configure()
            self.copy_patches()
            print("[BUILD FLATBACK]")
            self.build()
            print("[BUNDLE]")
            self.bundle()
            # No error, clean intermediate file at end of build if needed.
            print("[CLEAN]")
            if option('clean_at_end'):
                for platform in PlatformInfo.all_running_platforms.values():
                    platform.clean_intermediate_directories()
            else:
                print("SKIP")
        except StopBuild:
            sys.exit("Stopping build due to errors")

