from .base import (
    Dependency,
    Source,
    Builder,
    ReleaseDownload,
    GitClone,
    MesonBuilder,
    CMakeBuilder,
    QMakeBuilder,
    MakeBuilder,
    SCRIPT_DIR)
from kiwixbuild.utils import pj, run_command, REMOTE_PREFIX
from kiwixbuild._global import neutralEnv
from shutil import copyfile
import json
import os

class KiwixDesktopFlatpak(Dependency):
    name = "kiwix-desktop-flatpak"
    flatpak = {
        'remote': {
            'name': 'flathub',
            'url': 'https://flathub.org/repo/flathub.flatpakrepo'
        },
        'manifest': {
            'id': 'org.kiwix.Client',
            'runtime': 'org.kde.Platform',
            'runtime-version': '5.11',
            'sdk': 'org.kde.Sdk',
            'command': 'kiwix-desktop',
            'finish-args': [
                '--socket=wayland',
                '--socket=x11',
                '--share=ipc',
                '--device=dri',
                '--socket=pulseaudio'
            ],
            'cleanup': [
                '/include',
                '/lib/pkgconfig',
                '/lib/cmake',
                '/lib/*.la',
                '/bin/aria2c',
                '/bin/copydatabase',
                '/bin/kiwix-compile-resources',
                '/bin/quest',
                '/bin/simple*',
                '/bin/xapian-*',
                '/share/aclocal',
                '/share/doc',
                '/share/man'
            ]
        },
        'dependencies': ['kiwix-desktop']
    }
    # This will be configured during Source.prepare step
    flatpak_dir = ''
    flatpak_env = {}

    class Source(Source):
        def _setup_flatpak(self):
            flatpak_dir = pj(neutralEnv('toolchain_dir'), 'flatpak')
            os.makedirs(flatpak_dir, exist_ok=True)
            flatpak_env = {
                'FLATPAK_USER_DIR': flatpak_dir
            }
            self.target.flatpak_dir = flatpak_dir
            self.target.flatpak_env = flatpak_env

        def _remote(self, context):
            command = "flatpak --user remote-add --if-not-exists {remote_name} {remote_url}"
            command = command.format(
                remote_name = self.target.flatpak['remote']['name'],
                remote_url = self.target.flatpak['remote']['url']
            )
            run_command(command, '.', context, None, self.target.flatpak_env)

        def _runtimes(self, context):
            command = "flatpak --user install -y {remote_name} {sdk}//{version} {platform}//{version}"
            command = command.format(
                remote_name = self.target.flatpak['remote']['name'],
                sdk = self.target.flatpak['manifest']['sdk'],
                platform = self.target.flatpak['manifest']['runtime'],
                version = self.target.flatpak['manifest']['runtime-version']
            )
            run_command(command, '.', context, None, self.target.flatpak_env)

        def prepare(self):
            self._setup_flatpak()
            self.command('remote', self._remote)
            self.command('runtimes', self._runtimes)

    class Builder(Builder):
        def _get_all_dependencies(self, dependencies, platformInfo, all_deps):
            packages = []
            for package in dependencies:
                dep = all_deps[package]
                deps = dep.Builder.get_dependencies(platformInfo, all_deps)
                sub_packages = self._get_all_dependencies(deps, platformInfo, all_deps)
                packages += [package] + sub_packages
            return packages

        def _generate_modules(self, deps):
            modules = []
            for dep in deps:
                module = self._generate_module(dep)
                modules.append(module)
            return modules

        def _generate_module(self, dep):
            module = {
                'name': dep.name
            }

            # buildsystem and builddir
            if issubclass(dep.Builder, MesonBuilder):
                module['buildsystem'] = 'meson'
                module['builddir'] = True
            elif issubclass(dep.Builder, CMakeBuilder):
                module['buildsystem'] = 'cmake'
                module['builddir'] = True
            elif issubclass(dep.Builder, QMakeBuilder):
                module['buildsystem'] = 'qmake'

            # no-autogen
            if hasattr(dep.Source, 'flatpak_no_autogen'):
                module['no-autogen'] = dep.Source.flatpak_no_autogen

            # config-opts
            if hasattr(dep.Builder, 'configure_option') and \
                isinstance(dep.Builder.configure_option, str) and \
                dep.Builder.configure_option != '':
                module['config-opts'] = dep.Builder.configure_option.split(' ')

            sources = self._generate_sources(dep)
            module['sources'] = sources

            return module

        def _generate_sources(self, dep):
            sources = []
            # archive and git
            if issubclass(dep.Source, ReleaseDownload):
                source = {
                    'type': 'archive',
                    'sha256': dep.Source.archive.sha256
                }

                if dep.Source.archive.url != None:
                    source['url'] = dep.Source.archive.url
                else:
                    source['url'] = REMOTE_PREFIX + dep.Source.archive.name

                if hasattr(dep.Source, 'flatpak_dest'):
                    source['dest'] = dep.Source.flatpak_dest
                sources = [source]
            elif issubclass(dep.Source, GitClone):
                source = {
                    'type': 'git',
                    'url': dep.Source.git_remote,
                    'tag': dep.version()
                }
                sources = [source]

            # patches
            if hasattr(dep.Source, 'patches'):
                for p in dep.Source.patches:
                    patch = {
                        'type': 'patch',
                        'path': 'patches/' + p
                    }
                    sources += [patch]

            # shell
            if hasattr(dep.Source, 'flatpak_command'):
                source = {
                    'type': 'shell',
                    'commands': [
                        dep.Source.flatpak_command
                    ]
                }
                sources += [source]

            return sources

        def _copy_patches(self, deps):
            for dep in deps:
                if hasattr(dep.Source, 'patches'):
                    for p in dep.Source.patches:
                        path = pj(SCRIPT_DIR, 'patches', p)
                        os.makedirs(pj(self.build_path, 'patches'), exist_ok=True)
                        dest = pj(self.build_path, 'patches', p)
                        copyfile(path, dest)

        def _configure(self, context):
            os.makedirs(self.build_path, exist_ok=True)

            # get dependencies
            packages = self._get_all_dependencies(self.target.flatpak['dependencies'], self.buildEnv.platformInfo, Dependency.all_deps)
            deps = []
            for package in packages:
                deps.append(Dependency.all_deps[package])
            deps.reverse()

            # build manifest
            manifest = self.target.flatpak['manifest']
            modules = self._generate_modules(deps)
            manifest['modules'] = modules

            # write manifest
            file = open(pj(self.build_path, 'manifest.json'),'w')
            file.write(json.dumps(manifest, indent=4))
            file.close()

            self._copy_patches(deps)

        def _build(self, context):
            command = "flatpak-builder --ccache --force-clean --repo=repo builddir manifest.json"
            run_command(command, self.build_path, context, None, self.target.flatpak_env)

        def _bundle(self, context):
            command = "flatpak build-bundle repo {id}.flatpak {id}"
            command = command.format(
                id = self.target.flatpak['manifest']['id']
            )
            run_command(command, self.build_path, context, None, self.target.flatpak_env)

        def build(self):
            self.command('configure', self._configure)
            self.command('build', self._build)
            self.command('bundle', self._bundle)

        def make_dist(self):
            pass