
import os
import subprocess

from kiwixbuild.dependencies import Dependency
from kiwixbuild.toolchains import Toolchain
from kiwixbuild.packages import PACKAGE_NAME_MAPPERS
from kiwixbuild.utils import pj, remove_duplicates
from kiwixbuild.buildenv import BuildEnv
from kiwixbuild._global import neutralEnv, option, add_plt_step, target_steps

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
    def get_platform(cls, name):
        if name not in cls.all_running_platforms:
            cls.all_running_platforms[name] = cls.all_platforms[name]()
        return cls.all_running_platforms[name]

    def __init__(self):
        if neutralEnv('distname') not in self.compatible_hosts:
            print(('ERROR: The target platform {} cannot be build on host {}.\n'
                   'Select another target platform, or change your host system.'
                  ).format(self.name, neutralEnv('distname')))
            sys.exit(-1)
        self.all_running_platforms[self.name] = self
        self.buildEnv = BuildEnv(self)
        self.setup_toolchains()

    def __str__(self):
        return "{}_{}".format(self.build, 'static' if self.static else 'dyn')

    def setup_toolchains(self):
        self.toolchains = {}
        for tlc_name in self.toolchain_names:
            ToolchainClass = Toolchain.all_toolchains[tlc_name]
            self.toolchains[tlc_name] = ToolchainClass()
            if ToolchainClass.Source is not None:
                add_plt_step(('source', tlc_name), ToolchainClass.Source)
            if ToolchainClass.Builder is not None:
                plt_name = 'neutral' if ToolchainClass.neutral else self.name
                add_plt_step((plt_name, tlc_name), ToolchainClass.Builder)

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
        self.buildEnv.toolchains = [
            self.toolchains[tlc_name] for tlc_name in self.toolchain_names]
        self.buildEnv.cross_config = self.get_cross_config()
        self.buildEnv.meson_crossfile = None
        self.buildEnv.cmake_crossfile = None

    def get_packages(self):
        mapper_name = "{host}_{target}".format(
            host=neutralEnv('distname'),
            target=self)
        try:
            package_name_mapper = PACKAGE_NAME_MAPPERS[mapper_name]
        except KeyError:
            print("SKIP : We don't know which packages we must install to compile"
                  " a {target} {build_type} version on a {host} host.".format(
                      target=self.platform_info,
                      host=neutralEnv('distname')))
            return

        packages_list = package_name_mapper.get('COMMON', [])
        to_drop = []
        build_steps = (step for step in target_steps() if step[0] == self.name)
        for dep in build_steps:
            packages = package_name_mapper.get(dep[1])
            if packages:
                packages_list += packages
                to_drop.append(dep)
        for dep in to_drop:
            del target_steps()[dep]
        source_dep = [dep[1] for dep in target_steps() if dep[0] == 'source']
        for dep in source_dep:
            it_build = (True for dep in target_steps() if dep[0] != 'source' and dep[1] == dep)
            if next(it_build, False):
                print("removing source ", dep)
                del target_steps()[('source', dep)]
        build_steps = (step for step in target_steps() if step[0] == self.name)
        for dep in build_steps:
            packages = getattr(dep, 'extra_packages', [])
            for package in packages:
                packages_list += package_name_mapper.get(package, [])
        return packages_list

    def install_packages(self):
        autoskip_file = pj(self.buildEnv.build_dir, ".install_packages_ok")
        packages_to_have = self.get_packages()
        packages_to_have = remove_duplicates(packages_to_have)

        if not option('force_install_packages') and os.path.exists(autoskip_file):
            print("SKIP")
            return

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

        with open(autoskip_file, 'w'):
            pass

    def clean_intermediate_directories(self):
        self.buildEnv.clean_intermediate_directories()

