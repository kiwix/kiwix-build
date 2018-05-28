
import sys
from collections import OrderedDict
from .buildenv import *

from .platforms import PlatformInfo
from .utils import remove_duplicates, StopBuild
from .dependencies import Dependency
from ._global import (
    neutralEnv, option,
    add_target_step, get_target_step, target_steps,
    add_plt_step, get_plt_step, plt_steps)
from . import _global

class Builder:
    def __init__(self):
        platformClass = PlatformInfo.all_platforms[option('target_platform')]
        if neutralEnv('distname') not in platformClass.compatible_hosts:
            print(('ERROR: The target platform {} cannot be build on host {}.\n'
                   'Select another target platform, or change your host system.'
                  ).format(option('target_platform'), self.distname))
            sys.exit(-1)
        self.platform = platform = platformClass()

        _targets = {}
        targetDef = (option('target_platform'), option('targets'))
        self.add_targets(targetDef, _targets)
        dependencies = self.order_dependencies(_targets, targetDef)
        dependencies = list(remove_duplicates(dependencies))

        if option('build_nodeps'):
            add_target_step(targetDef, _targets[targetDef])
        else:
            for dep in dependencies:
                if option('build_deps_only') and dep == targetDef:
                    continue
                add_target_step(dep, _targets[dep])

    def add_targets(self, targetDef, targets):
        if targetDef in targets:
            return
        targetPlatformName, targetName = targetDef
        targetPlatform = PlatformInfo.all_platforms[targetPlatformName]
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
        targetPlatformName, targetName = targetDef
        if targetPlatformName == 'source':
            # Do not try to order sources, they will be added as dep by the
            # build step two lines later.
            return
        target = _targets[targetDef]
        targetPlatform = PlatformInfo.all_platforms[targetPlatformName]
        yield ('source', targetName)
        for dep in target.get_dependencies(targetPlatform):
            try:
                depPlatform, depName = dep
            except ValueError:
                depPlatform, depName = targetPlatformName, dep
            yield from self.order_dependencies(_targets, (depPlatform, depName))
        yield targetDef

    def prepare_toolchain_sources(self):
        tlsourceDefs = (tlDef for tlDef in plt_steps() if tlDef[0]=='source')
        for tlsourceDef in tlsourceDefs:
            print("prepare sources for toolchain {} :".format(tlsourceDef[1]))
            toolchainClass = Toolchain.all_toolchains[tlsourceDef[1]]
            source = get_plt_step(tlsourceDef)(toolchainClass)
            add_plt_step(tlsourceDef, source)
            source.prepare()

    def prepare_sources(self):
        if option('skip_source_prepare'):
            print("SKIP")
            return

        sourceDefs = remove_duplicates(tDef for tDef in target_steps() if tDef[0]=='source')
        for sourceDef in sourceDefs:

            print("prepare sources {} :".format(sourceDef[1]))
            depClass = Dependency.all_deps[sourceDef[1]]
            source = get_target_step(sourceDef)(depClass)
            add_target_step(sourceDef, source)
            source.prepare()

    def build_toolchains(self):
        tlbuilderDefs = (tlDef for tlDef in plt_steps() if tlDef[0] != 'source')
        for tlbuilderDef in tlbuilderDefs:
            print("build toolchain {} :".format(tlbuilderDef[1]))
            toolchainClass = Toolchain.all_toolchains[tlbuilderDef[1]]
            source = get_plt_step(tlbuilderDef[1], 'source')
            if tlbuilderDef[0] == 'neutral':
                env = _global._neutralEnv
            else:
                env = PlatformInfo.all_running_platforms[tlbuilderDef[0]].buildEnv
            builder = get_plt_step(tlbuilderDef)(toolchainClass, source, env)
            add_plt_step(tlbuilderDef, builder)
            builder.build()

    def build(self):
        builderDefs = (tDef for tDef in target_steps() if tDef[0] != 'source')
        for builderDef in builderDefs:
            depClass = Dependency.all_deps[builderDef[1]]
            source = get_target_step(builderDef[1], 'source')
            env = PlatformInfo.all_running_platforms[builderDef[0]].buildEnv
            builder = get_target_step(builderDef)(depClass, source, env)
            if option('make_dist') and builderDef[1] == option('targets'):
                print("make dist {}:".format(builder.name))
                builder.make_dist()
                continue
            print("build {} ({}):".format(builder.name, builderDef[0]))
            add_target_step(builderDef, builder)
            builder.build()


    def run(self):
        try:
            print("[SETUP PLATFORMS]")
            self.prepare_toolchain_sources()
            self.build_toolchains()
            self.platform.finalize_setup()
            print("[INSTALL PACKAGES]")
            self.platform.install_packages()
            print("[PREPARE]")
            self.prepare_sources()
            print("[BUILD]")
            self.build()
            # No error, clean intermediate file at end of build if needed.
            print("[CLEAN]")
            if option('clean_at_end'):
                self.platform.clean_intermediate_directories()
            else:
                print("SKIP")
        except StopBuild:
            sys.exit("Stopping build due to errors")

