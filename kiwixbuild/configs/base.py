import os
from typing import ClassVar

from kiwixbuild._global import option
from kiwixbuild.buildenv import BuildEnv
from kiwixbuild.dependencies import Dependency
from kiwixbuild.utils import DefaultEnv, pj

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATES_DIR = pj(os.path.dirname(_SCRIPT_DIR), "templates")


class _MetaConfig(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name not in ("ConfigInfo", "MetaConfigInfo") and "name" in dct:
            dep_name = dct["name"]
            ConfigInfo.all_configs[dep_name] = _class
        return _class


class ConfigInfo(metaclass=_MetaConfig):
    all_configs: ClassVar[dict] = {}
    all_running_configs: ClassVar[dict] = {}
    toolchain_names: ClassVar[list] = []
    configure_options: ClassVar[list] = []
    mixed = False
    libdir = None

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
        return "{}_{}".format(self.build, "static" if self.static else "dyn")

    def setup_toolchains(self, targets):
        for tlc_name in self.toolchain_names:
            toolchain_class = Dependency.all_deps[tlc_name]
            targets[("source", tlc_name)] = toolchain_class.Source
            cfg_name = "neutral" if toolchain_class.neutral else self.name
            targets[(cfg_name, tlc_name)] = toolchain_class.Builder

    def add_targets(self, target_name, targets):
        if (self.name, target_name) in targets:
            return []
        target_class = Dependency.all_deps[target_name]
        targets[("source", target_name)] = target_class.Source
        targets[(self.name, target_name)] = target_class.Builder
        for dep in target_class.Builder.get_dependencies(self, False):
            if isinstance(dep, tuple):
                dep_config_name, dep_name = dep
            else:
                dep_config_name, dep_name = self.name, dep
            dep_config = self.get_config(dep_config_name, targets)
            dep_config.add_targets(dep_name, targets)
        return [(self.name, target_name)]

    def get_fully_qualified_dep(self, dep):
        if isinstance(dep, tuple):
            return dep
        else:
            return self.name, dep

    def get_cross_config(self):
        return {}

    def get_include_dirs(self):
        return [pj(self.buildEnv.install_dir, "include")]

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
        crossfile = pj(self.buildEnv.build_dir, outname)
        template_file = pj(TEMPLATES_DIR, name)
        with open(template_file) as f:
            template = f.read()
        content = template.format(**self.get_cross_config())
        with open(crossfile, "w") as outfile:
            outfile.write(content)
        return crossfile

    def finalize_setup(self):
        self.buildEnv.cross_config = self.get_cross_config()
        self.buildEnv.meson_crossfile = None
        self.buildEnv.cmake_crossfile = None

    def clean_intermediate_directories(self):
        self.buildEnv.clean_intermediate_directories()


class MetaConfigInfo(ConfigInfo):
    sub_config_names: ClassVar[list] = []

    def add_targets(self, target_name, targets):
        target_defs = []
        for config_name in self.sub_config_names:
            config = self.get_config(config_name, targets)
            target_defs += config.add_targets(target_name, targets)
        return target_defs


def mixed_mixin(static_name):
    class MixedMixinClass:
        mixed = True
        static = False

        def add_targets(self, target_name, targets):
            if option("target") == target_name:
                return super().add_targets(target_name, targets)
            else:
                static_config = self.get_config(static_name, targets)
                return static_config.add_targets(target_name, targets)

        def get_fully_qualified_dep(self, dep):
            if isinstance(dep, tuple):
                return dep
            if option("target") == dep:
                return self.name, dep
            return static_name, dep

        @property
        def static_build_env(self):
            static_config = self.get_config(static_name)
            return static_config.buildEnv

        def get_include_dirs(self):
            return [
                pj(self.buildEnv.install_dir, "include"),
                pj(self.static_build_env.install_dir, "include"),
            ]

        def get_env(self):
            env = super().get_env()
            env["PATH"].insert(0, pj(self.static_build_env.install_dir, "bin"))
            pkgconfig_path = pj(
                self.static_build_env.install_dir,
                self.static_build_env.libprefix,
                "pkgconfig",
            )
            env["PKG_CONFIG_PATH"].append(pkgconfig_path)
            env["CPPFLAGS"] = " ".join(
                [
                    "-I" + pj(self.static_build_env.install_dir, "include"),
                    env["CPPFLAGS"],
                ]
            )
            return env

    return MixedMixinClass
