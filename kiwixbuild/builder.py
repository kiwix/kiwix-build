import subprocess
import sys

from ._global import (
    add_target_step,
    get_target_step,
    neutral_env,
    option,
    target_steps,
)
from .configs import ConfigInfo
from .dependencies import Dependency
from .packages import PACKAGE_NAME_MAPPERS
from .utils import StopBuild, colorize, remove_duplicates


class Builder:
    def __init__(self):
        self._targets = {}
        ConfigInfo.get_config("neutral", self._targets)

        config_name = option("config")
        config = ConfigInfo.get_config(config_name, self._targets)
        if neutral_env("distname") not in config.compatible_hosts:
            print(
                (
                    colorize("ERROR") + ": The config {} cannot be build on host {}.\n"
                    "Select another config or change your host system."
                ).format(config.name, neutral_env("distname"))
            )
        self.targetDefs = config.add_targets(option("target"), self._targets)

    def finalize_target_steps(self):
        steps = []
        for target_def in self.targetDefs:
            steps += self.order_steps(target_def)
        steps = list(remove_duplicates(steps))

        if option("build_nodeps"):
            # add all config steps
            for dep in steps:
                step_class = Dependency.all_deps[dep[1]]
                if step_class.dont_skip:
                    add_target_step(dep, self._targets[dep])

            src_target_def = ("source", target_def[1])
            add_target_step(src_target_def, self._targets[src_target_def])
            add_target_step(target_def, self._targets[target_def])
        else:
            for dep in steps:
                if option("build_deps_only") and dep[1] == target_def[1]:
                    continue
                add_target_step(dep, self._targets[dep])
        self.instanciate_steps()

    def order_steps(self, target_def):
        for cfg_name in ConfigInfo.all_running_configs:
            cfg = ConfigInfo.all_configs[cfg_name]
            for tlc_name in cfg.toolchain_names:
                tlc = Dependency.all_deps[tlc_name]
                yield ("source", tlc_name)
                yield ("neutral" if tlc.neutral else cfg_name, tlc_name)
        _targets = dict(self._targets)
        yield from self.order_dependencies(target_def, _targets)

    def order_dependencies(self, target_def, targets):
        target_config_name, target_name = target_def
        if target_config_name == "source":
            # Do not try to order sources, they will be added as dep by the
            # build step two lines later.
            return
        try:
            target = targets.pop(target_def)
        except KeyError:
            return

        target_config = ConfigInfo.get_config(target_config_name)
        for dep in target.get_dependencies(target_config, True):
            dep_config, dep_name = target_config.get_fully_qualified_dep(dep)
            if (dep_config, dep_name) in targets:
                yield from self.order_dependencies((dep_config, dep_name), targets)
        yield ("source", target_name)
        yield target_def

    def instanciate_steps(self):
        for step_def in list(target_steps()):
            step_config, step_name = step_def
            step_class = Dependency.all_deps[step_name]
            if step_config == "source":
                source = get_target_step(step_def)(step_class)
                add_target_step(step_def, source)
            else:
                source = get_target_step(step_name, "source")
                env = ConfigInfo.get_config(step_config).buildEnv
                builder = get_target_step(step_def)(step_class, source, env)
                add_target_step(step_def, builder)

    def prepare_sources(self):
        if option("skip_source_prepare"):
            print(colorize("SKIP"))
            return

        source_defs = remove_duplicates(
            tDef for tDef in target_steps() if tDef[0] == "source"
        )
        for source_def in source_defs:
            print(f"prepare sources {source_def[1]} :")
            source = get_target_step(source_def)
            source.prepare()

    def build(self):
        builder_defs = (tDef for tDef in target_steps() if tDef[0] != "source")
        for builder_def in builder_defs:
            builder = get_target_step(builder_def)
            if option("make_dist") and builder_def[1] == option("target"):
                print(f"make dist {builder.name} ({builder_def[0]}):")
                builder.make_dist()
                continue
            print(f"build {builder.name} ({builder_def[0]}):")
            add_target_step(builder_def, builder)
            builder.build()

    def _get_packages(self):
        packages_list = []
        for running_config in ConfigInfo.all_running_configs.values():
            for mapper_name in self._get_mapper_names_for_config(running_config):
                package_name_mapper = PACKAGE_NAME_MAPPERS.get(mapper_name, {})
                packages_list += package_name_mapper.get("COMMON", [])

        to_drop = []
        for builder_def in self._targets:
            builder_config, builder_name = builder_def

            for mapper_name in self._get_mapper_names_for_config(builder_config):
                package_name_mapper = PACKAGE_NAME_MAPPERS.get(mapper_name, {})
                packages = package_name_mapper.get(builder_name)
                if packages:
                    to_drop.append(builder_def)
                    if packages is not True:
                        # True means "assume the dependency is install but do
                        # not try to install anything for it"
                        packages_list += packages

        for dep in to_drop:
            del self._targets[dep]
        return packages_list

    def _get_mapper_names_for_config(self, config):
        host = neutral_env("distname")
        codename = neutral_env("codename")
        yield f"{host}_{config}"
        if codename != "":
            yield f"{host}_{codename}_{config}"

    def install_packages(self):
        packages_to_have = self._get_packages()
        packages_to_have = remove_duplicates(packages_to_have)

        if option("assume_packages_installed"):
            print(colorize("SKIP") + ", Assume package installed")
            return

        distname = neutral_env("distname")
        if distname in ("fedora", "redhat", "centos"):
            package_installer = "sudo dnf install {}"
            package_checker = "rpm -q --quiet {}"
        elif distname in ("debian", "ubuntu"):
            package_installer = "sudo apt-get install {}"
            package_checker = 'LANG=C dpkg -s {} 2>&1 | grep Status | grep "ok installed" 1>/dev/null 2>&1'
        elif distname == "Darwin":
            package_installer = "brew install {}"
            package_checker = "brew ls --version {} > /dev/null"

        packages_to_install = []
        for package in packages_to_have:
            print(f" - {package} : ", end="")
            command = package_checker.format(package)
            try:
                subprocess.check_call(command, shell=True)  # noqa: S602
            except subprocess.CalledProcessError:
                print(colorize("NEEDED"))
                packages_to_install.append(package)
            else:
                print(colorize("SKIP"))

        if packages_to_install:
            command = package_installer.format(" ".join(packages_to_install))
            print(command)
            subprocess.check_call(command, shell=True)  # noqa: S602
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
