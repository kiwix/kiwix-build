
import sys
from collections import OrderedDict
from .buildenv import *

from .platforms import PlatformInfo
from .utils import remove_duplicates, StopBuild
from .dependencies import Dependency
from .packages import PACKAGE_NAME_MAPPERS
from ._global import (
    neutralEnv, option,
    add_target_step, get_target_step, target_steps)
from . import _global

class Builder:
    def __init__(self):
        self._targets = {}
        PlatformInfo.get_platform('neutral', self._targets)

        target_platform = option('target_platform')
        if not target_platform:
            if option('target') == 'kiwix-android':
                target_platform = 'android'
            else:
                target_platform = 'native_dyn'
        platform = PlatformInfo.get_platform(target_platform, self._targets)
        self.targetDefs = platform.add_targets(option('target'), self._targets)

    def finalize_target_steps(self):
        steps = []
        for targetDef in self.targetDefs:
            steps += self.order_steps(targetDef)
        steps = list(remove_duplicates(steps))

        if option('build_nodeps'):
            add_target_step(targetDef, self._targets[targetDef])
        else:
            for dep in steps:
                if option('build_deps_only') and dep == targetDef:
                    continue
                add_target_step(dep, self._targets[dep])
        self.instanciate_steps()

    def order_steps(self, targetDef):
        for pltName in PlatformInfo.all_running_platforms:
            plt = PlatformInfo.all_platforms[pltName]
            for tlcName in plt.toolchain_names:
                tlc = Dependency.all_deps[tlcName]
                yield('source', tlcName)
                yield('neutral' if tlc.neutral else pltName, tlcName)
        _targets =dict(self._targets)
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
            try:
                depPlatform, depName = dep
            except ValueError:
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

    def prepare_sources(self):
        if option('skip_source_prepare'):
            print("SKIP")
            return

        sourceDefs = remove_duplicates(tDef for tDef in target_steps() if tDef[0]=='source')
        for sourceDef in sourceDefs:
            print("prepare sources {} :".format(sourceDef[1]))
            source = get_target_step(sourceDef)
            source.prepare()

    def build(self):
        builderDefs = (tDef for tDef in target_steps() if tDef[0] != 'source')
        for builderDef in builderDefs:
            builder = get_target_step(builderDef)
            if option('make_dist') and builderName == option('target'):
                print("make dist {} ({}):".format(builder.name, builderDef[0]))
                builder.make_dist()
                continue
            print("build {} ({}):".format(builder.name, builderDef[0]))
            add_target_step(builderDef, builder)
            builder.build()

    def _get_packages(self):
        packages_list = []
        for platform in PlatformInfo.all_running_platforms.values():
            mapper_name = "{host}_{target}".format(
                host=neutralEnv('distname'),
                target=platform)
            package_name_mapper = PACKAGE_NAME_MAPPERS.get(mapper_name, {})
            packages_list += package_name_mapper.get('COMMON', [])

        to_drop = []
        for builderDef in self._targets:
            platformName, builderName = builderDef
            mapper_name = "{host}_{target}".format(
                host=neutralEnv('distname'),
                target=platformName)
            package_name_mapper = PACKAGE_NAME_MAPPERS.get(mapper_name, {})
            packages = package_name_mapper.get(builderName)
            if packages:
                packages_list += packages
                to_drop.append(builderDef)
        for dep in to_drop:
            del self._targets[dep]
        return packages_list

    def install_packages(self):
        packages_to_have = self._get_packages()
        packages_to_have = remove_duplicates(packages_to_have)

        distname = neutralEnv('distname')
        if distname in ('fedora', 'redhat', 'centos'):
            package_installer = 'sudo dnf install {}'
            package_checker = 'rpm -q --quiet {}'
        elif distname in ('debian', 'Ubuntu'):
            package_installer = 'sudo apt-get install {}'
            package_checker = 'LANG=C dpkg -s {} 2>&1 | grep Status | grep "ok installed" 1>/dev/null 2>&1'
        elif distname == 'Darwin':
            package_installer = 'brew install {}'
            package_checker = 'brew list -1 | grep -q {}'

        packages_to_install = []
        for package in packages_to_have:
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

    def run(self):
        try:
            print("[INSTALL PACKAGES]")
            if option('dont_install_packages'):
                print("SKIP")
            else:
                self.install_packages()
            self.finalize_target_steps()
            print("[SETUP PLATFORMS]")
            for platform in PlatformInfo.all_running_platforms.values():
                platform.finalize_setup()
            print("[PREPARE]")
            self.prepare_sources()
            print("[BUILD]")
            self.build()
            # No error, clean intermediate file at end of build if needed.
            print("[CLEAN]")
            if option('clean_at_end'):
                for platform in PlatformInfo.all_running_platforms.values():
                    platform.clean_intermediate_directories()
            else:
                print("SKIP")
        except StopBuild:
            sys.exit("Stopping build due to errors")

