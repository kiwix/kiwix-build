
import os, sys
import subprocess

from kiwixbuild.dependencies import Dependency
from kiwixbuild.utils import pj, remove_duplicates
from kiwixbuild.buildenv import BuildEnv
from kiwixbuild._global import neutralEnv, option, target_steps

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATES_DIR = pj(os.path.dirname(_SCRIPT_DIR), 'templates')

class _MetaPlatform(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name not in ('PlatformInfo', 'MetaPlatformInfo') and 'name' in dct:
            dep_name = dct['name']
            PlatformInfo.all_platforms[dep_name] = _class
        return _class


class PlatformInfo(metaclass=_MetaPlatform):
    all_platforms = {}
    all_running_platforms = {}
    toolchain_names = []
    configure_option = ""

    @classmethod
    def get_platform(cls, name, targets=None):
        if name not in cls.all_running_platforms:
            if targets is None:
                print("Should not got there.")
                print(cls.all_running_platforms)
                raise KeyError(name)
            cls.all_running_platforms[name] = cls.all_platforms[name](targets)
        return cls.all_running_platforms[name]

    def __init__(self, targets):
        self.all_running_platforms[self.name] = self
        self.buildEnv = BuildEnv(self)
        self.setup_toolchains(targets)

    def __str__(self):
        return "{}_{}".format(self.build, 'static' if self.static else 'dyn')

    def setup_toolchains(self, targets):
        for tlc_name in self.toolchain_names:
            ToolchainClass = Dependency.all_deps[tlc_name]
            targets[('source', tlc_name)] = ToolchainClass.Source
            plt_name = 'neutral' if ToolchainClass.neutral else self.name
            targets[(plt_name, tlc_name)] = ToolchainClass.Builder

    def add_targets(self, targetName, targets):
        if (self.name, targetName) in targets:
            return []
        targetClass = Dependency.all_deps[targetName]
        targets[('source', targetName)] = targetClass.Source
        targets[(self.name, targetName)] = targetClass.Builder
        for dep in targetClass.Builder.get_dependencies(self, False):
            if isinstance(dep, tuple):
                depPlatformName, depName = dep
            else:
                depPlatformName, depName = self.name, dep
            depPlatform = self.get_platform(depPlatformName, targets)
            depPlatform.add_targets(depName, targets)
        return [(self.name, targetName)]

    def get_cross_config(self):
        return {}

    def set_env(self, env):
        pass

    def get_bind_dir(self):
        return []

    def set_compiler(self, env):
        pass

    def _gen_crossfile(self, name):
        crossfile = pj(self.buildEnv.build_dir, name)
        template_file = pj(TEMPLATES_DIR, name)
        with open(template_file, 'r') as f:
            template = f.read()
        content = template.format(
            **self.get_cross_config()
        )
        with open(crossfile, 'w') as outfile:
            outfile.write(content)
        return crossfile

    def finalize_setup(self):
        self.buildEnv.cross_config = self.get_cross_config()
        self.buildEnv.meson_crossfile = None
        self.buildEnv.cmake_crossfile = None

    def clean_intermediate_directories(self):
        self.buildEnv.clean_intermediate_directories()



class MetaPlatformInfo(PlatformInfo):
    subPlatformNames = []

    def add_targets(self, targetName, targets):
        targetDefs = []
        for platformName in self.subPlatformNames:
            print("radd {}".format(platformName))
            platform = self.get_platform(platformName, targets)
            targetDefs += platform.add_targets(targetName, targets)
        return targetDefs
