
import sys
from collections import OrderedDict
from .buildenv import *

from .platforms import PlatformInfo
from .utils import remove_duplicates, StopBuild
from .dependencies import Dependency
from ._global import (
    neutralEnv, option,
    add_target_step, get_target_step, target_steps)
from . import _global

class Builder:
    def __init__(self):
        _targets = {}
        targetDef = (option('target_platform'), option('targets'))
        self.add_targets(targetDef, _targets)
        dependencies = self.order_dependencies(_targets, targetDef)
        dependencies = list(remove_duplicates(dependencies))

        PlatformInfo.get_platform('neutral', _targets)
        if option('build_nodeps'):
            add_target_step(targetDef, _targets[targetDef])
        else:
            for dep in dependencies:
                if option('build_deps_only') and dep == targetDef:
                    continue
                add_target_step(dep, _targets[dep])
        self.instanciate_steps()

    def add_targets(self, targetDef, targets):
        if targetDef in targets:
            return
        targetPlatformName, targetName = targetDef
        targetPlatform = PlatformInfo.get_platform(targetPlatformName, targets)
        targetClass = Dependency.all_deps[targetName]
        targets[('source', targetName)] = targetClass.Source
        targets[targetDef] = targetClass.Builder
        for dep in targetClass.Builder.get_dependencies(targetPlatform):
            try:
                depPlatform, depName = dep
            except ValueError:
                depPlatform, depName = targetPlatformName, dep
            self.add_targets((depPlatform, depName), targets)

    def order_dependencies(self, _targets, targetDef):
        for pltName in PlatformInfo.all_running_platforms:
            plt = PlatformInfo.all_platforms[pltName]
            for tlcName in plt.toolchain_names:
                tlc = Dependency.all_deps[tlcName]
                yield('source', tlcName)
                yield('neutral' if tlc.neutral else pltName, tlcName)
        targetPlatformName, targetName = targetDef
        if targetPlatformName == 'source':
            # Do not try to order sources, they will be added as dep by the
            # build step two lines later.
            return
        target = _targets[targetDef]
        targetPlatform = PlatformInfo.get_platform(targetPlatformName)
        yield ('source', targetName)
        for dep in target.get_dependencies(targetPlatform):
            try:
                depPlatform, depName = dep
            except ValueError:
                depPlatform, depName = targetPlatformName, dep
            yield from self.order_dependencies(_targets, (depPlatform, depName))
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
            if option('make_dist') and builderName == option('targets'):
                print("make dist {} ({}):".format(builder.name, builderDef[0]))
                builder.make_dist()
                continue
            print("build {} ({}):".format(builder.name, builderDef[0]))
            add_target_step(builderDef, builder)
            builder.build()


    def run(self):
        try:
            print("[SETUP PLATFORMS]")
            for platform in PlatformInfo.all_running_platforms.values():
                platform.finalize_setup()
            print("[INSTALL PACKAGES]")
            for platform in PlatformInfo.all_running_platforms.values():
                platform.install_packages()
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

