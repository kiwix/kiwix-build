import sys
from collections import OrderedDict
from .buildenv import *

from .configs import ConfigInfo
from .utils import remove_duplicates, StopBuild, colorize
from .dependencies import Dependency
from .packages import PACKAGE_NAME_MAPPERS
from ._global import (
    neutralEnv,
    option,
    add_target_step,
    get_target_step,
    target_steps,
)
from . import _global
import subprocess
import tarfile

class Builder:
    def __init__(self):
        self._targets = {}
        ConfigInfo.get_config("neutral", self._targets)

        config_name = option("config")
        config = ConfigInfo.get_config(config_name, self._targets)
        if neutralEnv("distname") not in config.compatible_hosts:
            print(
                (
                    colorize("ERROR") + ": The config {} cannot be build on host {}.\n"
                    "Select another config or change your host system."
                ).format(config.name, neutralEnv("distname"))
            )
        self.targetDefs = config.add_targets(option("target"), self._targets)

    def make_dist(self):
        build_output_dir = "/path/to/build/output"  # Replace with your actual output directory
        tarball_path = "/path/to/output/kiwix.tar.gz"  # Desired tarball location
        # Create the tarball
        print(f"Creating tarball at {tarball_path}")
        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(build_output_dir, arcname=os.path.basename(build_output_dir))
        print(f"Tarball created successfully: {tarball_path}")

        # Sign the tarball with GPG
        print(f"Signing tarball {tarball_path}")
        sig_command = ["gpg", "--detach-sign", tarball_path]
        try:
            subprocess.run(sig_command, check=True)
            print(f"Signature created: {tarball_path}.sig")
        except subprocess.CalledProcessError as e:
            print(f"Error signing tarball: {e}")

    def finalize_target_steps(self):
        steps = []
        for targetDef in self.targetDefs:
            steps += self.order_steps(targetDef)
        steps = list(remove_duplicates(steps))

        if option("build_nodeps"):
            # add all config steps
            for dep in steps:
                stepClass = Dependency.all_deps[dep[1]]
                if stepClass.dont_skip:
                    add_target_step(dep, self._targets[dep])

            src_targetDef = ("source", targetDef[1])
            add_target_step(src_targetDef, self._targets[src_targetDef])
            add_target_step(targetDef, self._targets[targetDef])
        else:
            for dep in steps:
                if option("build_deps_only") and dep[1] == targetDef[1]:
                    continue
                add_target_step(dep, self._targets[dep])
        self.instanciate_steps()

    def order_steps(self, targetDef):
        for cfgName in ConfigInfo.all_running_configs:
            cfg = ConfigInfo.all_configs[cfgName]
            for tlcName in cfg.toolchain_names:
                tlc = Dependency.all_deps[tlcName]
                yield ("source", tlcName)
                yield ("neutral" if tlc.neutral else cfgName, tlcName)
        _targets = dict(self._targets)
        yield from self.order_dependencies(targetDef, _targets)

    def order_dependencies(self, targetDef, targets):
        targetConfigName, targetName = targetDef
        if targetConfigName == "source":
            # Do not try to order sources, they will be added as dep by the
            # build step two lines later.
            return
        try:
            target = targets.pop(targetDef)
        except KeyError:
            return

        targetConfig = ConfigInfo.get_config(targetConfigName)
        for dep in target.get_dependencies(targetConfig, True):
            depConfig, depName = targetConfig.get_fully_qualified_dep(dep)
            if (depConfig, depName) in targets:
                yield from self.order_dependencies((depConfig, depName), targets)
        yield ("source", targetName)
        yield targetDef

    def instanciate_steps(self):
        for stepDef in list(target_steps()):
            stepConfig, stepName = stepDef
            stepClass = Dependency.all_deps[stepName]
            if stepConfig == "source":
                source = get_target_step(stepDef)(stepClass)
                add_target_step(stepDef, source)
            else:
                source = get_target_step(stepName, "source")
                env = ConfigInfo.get_config(stepConfig).buildEnv
                builder = get_target_step(stepDef)(stepClass, source, env)
                add_target_step(stepDef, builder)

    def prepare_sources(self):
        if option("skip_source_prepare"):
            print(colorize("SKIP"))
            return

        sourceDefs = remove_duplicates(
            tDef for tDef in target_steps() if tDef[0] == "source"
        )
        for sourceDef in sourceDefs:
            print("prepare sources {} :".format(sourceDef[1]))
            source = get_target_step(sourceDef)
            source.prepare()

    def build(self):
        builderDefs = (tDef for tDef in target_steps() if tDef[0] != "source")
        for builderDef in builderDefs:
            builder = get_target_step(builderDef)
            if option("make_dist") and builderDef[1] == option("target"):
                print("make dist {} ({}):".format(builder.name, builderDef[0]))
                try:
                    builder.make_dist()
                    print("Distribution tarball and signature created successfully.")
                except AttributeError:
                    print(f"ERROR: The target {builder.name} does not implement make_dist().")
                except Exception as e:
                    print(f"ERROR while creating tarball or signature: {e}")
                continue
            print(f"build {builder.name} ({builderDef[0]}):")
            add_target_step(builderDef, builder)
            try:
                builder.build()
            except Exception as e:
                print(f"ERROR during build of {builder.name}: {e}")

    def _get_packages(self):
        packages_list = []
        for config in ConfigInfo.all_running_configs.values():
            mapper_name = "{host}_{config}".format(
                host=neutralEnv("distname"), config=config
            )
            package_name_mapper = PACKAGE_NAME_MAPPERS.get(mapper_name, {})
            packages_list += package_name_mapper.get("COMMON", [])

        to_drop = []
        for builderDef in self._targets:
            configName, builderName = builderDef
            mapper_name = "{host}_{config}".format(
                host=neutralEnv("distname"), config=configName
            )
            package_name_mapper = PACKAGE_NAME_MAPPERS.get(mapper_name, {})
            packages = package_name_mapper.get(builderName)
            if packages:
                to_drop.append(builderDef)
                if packages is not True:
                    # True means "assume the dependency is install but do not try to install anything for it"
                    packages_list += packages
        for dep in to_drop:
            del self._targets[dep]
        return packages_list

    def install_packages(self):
        packages_to_have = self._get_packages()
        packages_to_have = remove_duplicates(packages_to_have)

        if option("assume_packages_installed"):
            print(colorize("SKIP") + ", Assume package installed")
            return

        distname = neutralEnv("distname")
        if distname in ("fedora", "redhat", "centos"):
            package_installer = "sudo dnf install {}"
            package_checker = "rpm -q --quiet {}"
        elif distname in ("debian", "Ubuntu"):
            package_installer = "sudo apt-get install {}"
            package_checker = 'LANG=C dpkg -s {} 2>&1 | grep Status | grep "ok installed" 1>/dev/null 2>&1'
        elif distname == "Darwin":
            package_installer = "brew install {}"
            package_checker = "brew ls --version {} > /dev/null"

        packages_to_install = []
        for package in packages_to_have:
            print(" - {} : ".format(package), end="")
            command = package_checker.format(package)
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError:
                print(colorize("NEEDED"))
                packages_to_install.append(package)
            else:
                print(colorize("SKIP"))

        if packages_to_install:
            command = package_installer.format(" ".join(packages_to_install))
            print(command)
            subprocess.check_call(command, shell=True)
        else:
            print(colorize("SKIP") + ", No package to install.")

    def run(self):
        try:
            print("[INSTALL PACKAGES]")
            if option("dont_install_packages"):
                print(colorize("SKIP"))
            else:
                self.install_packages()
            self.finalize_target_steps()
            print("[SETUP TOOLCHAINS]")
            for config in ConfigInfo.all_running_configs.values():
                config.finalize_setup()
            print("[PREPARE]")
            self.prepare_sources()
            print("[BUILD]")
            self.build()
            # No error, clean intermediate file at end of build if needed.
            print("[CLEAN]")
            if option("clean_at_end"):
                for config in ConfigInfo.all_running_configs.values():
                    config.clean_intermediate_directories()
            else:
                print(colorize("SKIP"))
        except StopBuild as e:
            print(e)
            sys.exit("Stopping build due to errors")
