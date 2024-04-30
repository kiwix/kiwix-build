import os, sys
import subprocess
from pathlib import Path

from kiwixbuild.dependencies import Dependency
from kiwixbuild.utils import remove_duplicates, DefaultEnv
from kiwixbuild.buildenv import BuildEnv
from kiwixbuild._global import neutralEnv, option, target_steps

_SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = _SCRIPT_DIR.parent / "templates"


class _MetaConfig(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name not in ("ConfigInfo", "MetaConfigInfo") and "name" in dct:
            dep_name = dct["name"]
            ConfigInfo.all_configs[dep_name] = _class
        return _class


class ConfigInfo(metaclass=_MetaConfig):
    all_configs = {}
    all_running_configs = {}
    toolchain_names = []
    configure_options = []
    mixed = False
    libdir = None
    force_posix_path = False

    @property
    def arch_name(self):
        return self.arch_full

    @classmethod
    def get_config(cls, name, targets=None):
        if name not in cls.all_running_configs:
            if targets is None:
                print("Should not got there.")
                print(cls.all_running_configs)
                raise KeyError(name)
            cls.all_running_configs[name] = cls.all_configs[name](targets)
        return cls.all_running_configs[name]

    def __init__(self, targets):
        self.all_running_configs[self.name] = self
        self.buildEnv = BuildEnv(self)
        self.setup_toolchains(targets)

    def __str__(self):
        postfix = "static" if self.static else "dyn"
        return f"{self.build}_{postfix}"

    def setup_toolchains(self, targets):
        for tlc_name in self.toolchain_names:
            ToolchainClass = Dependency.all_deps[tlc_name]
            targets[("source", tlc_name)] = ToolchainClass.Source
            cfg_name = "neutral" if ToolchainClass.neutral else self.name
            targets[(cfg_name, tlc_name)] = ToolchainClass.Builder

    def add_targets(self, targetName, targets):
        if (self.name, targetName) in targets:
            return []
        targetClass = Dependency.all_deps[targetName]
        targets[("source", targetName)] = targetClass.Source
        targets[(self.name, targetName)] = targetClass.Builder
        for dep in targetClass.Builder.get_dependencies(self, False):
            if isinstance(dep, tuple):
                depConfigName, depName = dep
            else:
                depConfigName, depName = self.name, dep
            depConfig = self.get_config(depConfigName, targets)
            depConfig.add_targets(depName, targets)
        return [(self.name, targetName)]

    def get_fully_qualified_dep(self, dep):
        if isinstance(dep, tuple):
            return dep
        else:
            return self.name, dep

    def get_cross_config(self):
        return {}

    def get_include_dirs(self):
        return [self.buildEnv.install_dir / "include"]

    def get_env(self):
        return DefaultEnv()

    def get_bin_dir(self):
        return []

    def set_compiler(self, env):
        pass

    def set_comp_flags(self, env):
        if self.static:
            env["CFLAGS"] = env["CFLAGS"] + " -fPIC"
            env["CXXFLAGS"] = env["CXXFLAGS"] + " -fPIC"

    def _gen_crossfile(self, name, outname=None):
        if outname is None:
            outname = name
        crossfile = self.buildEnv.build_dir / outname
        template_file = TEMPLATES_DIR / name
        template = template_file.read_text()
        content = template.format(**self.get_cross_config())
        crossfile.write_text(content)
        return crossfile

    def finalize_setup(self):
        self.buildEnv.cross_config = self.get_cross_config()
        self.buildEnv.meson_crossfile = None
        self.buildEnv.cmake_crossfile = None

    def clean_intermediate_directories(self):
        self.buildEnv.clean_intermediate_directories()


class MetaConfigInfo(ConfigInfo):
    subConfigNames = []

    def add_targets(self, targetName, targets):
        targetDefs = []
        for configName in self.subConfigNames:
            config = self.get_config(configName, targets)
            targetDefs += config.add_targets(targetName, targets)
        return targetDefs


def MixedMixin(static_name):
    class MixedMixinClass:
        mixed = True
        static = False

        def add_targets(self, targetName, targets):
            if option("target") == targetName:
                return super().add_targets(targetName, targets)
            else:
                static_config = self.get_config(static_name, targets)
                return static_config.add_targets(targetName, targets)

        def get_fully_qualified_dep(self, dep):
            if isinstance(dep, tuple):
                return dep
            if option("target") == dep:
                return self.name, dep
            return static_name, dep

        @property
        def static_buildEnv(self):
            static_config = self.get_config(static_name)
            return static_config.buildEnv

        def get_include_dirs(self):
            return [
                self.buildEnv.install_dir / "include",
                self.static_buildEnv.install_dir / "include",
            ]

        def get_env(self):
            env = super().get_env()
            env["PATH"].insert(0, self.static_buildEnv.install_dir / "bin")
            pkgconfig_path = (
                self.static_buildEnv.install_dir
                / self.static_buildEnv.libprefix
                / "pkgconfig"
            )
            env["PKG_CONFIG_PATH"].append(pkgconfig_path)
            env["CPPFLAGS"] = " ".join(
                [
                    f"-I{self.static_buildEnv.install_dir / 'include'}",
                    env["CPPFLAGS"],
                ]
            )
            return env

    return MixedMixinClass
