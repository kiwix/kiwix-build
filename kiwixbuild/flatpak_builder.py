import sys
from collections import OrderedDict
from .buildenv import *

from .configs import ConfigInfo
from .utils import remove_duplicates, run_command, StopBuild, Context
from .dependencies import Dependency
from .packages import PACKAGE_NAME_MAPPERS
from .versions import base_deps_versions
from ._global import (
    neutralEnv,
    option,
    add_target_step,
    get_target_step,
    target_steps,
)
from . import _global
from .dependencies.base import (
    Source,
    Builder,
    ReleaseDownload,
    GitClone,
    MesonBuilder,
    CMakeBuilder,
    QMakeBuilder,
    MakeBuilder,
    SCRIPT_DIR,
)
import json
from shutil import copyfile
from urllib.parse import urlparse
from urllib.request import urlopen
import json

MANIFEST = {
    "app-id": "org.kiwix.desktop",
    "runtime": "org.kde.Platform",
    "runtime-version": base_deps_versions["org.kde"],
    "base": "io.qt.qtwebengine.BaseApp",
    "base-version": base_deps_versions["io.qt.qtwebengine"],
    "sdk": "org.kde.Sdk",
    "command": "kiwix-desktop",
    "rename-icon": "kiwix-desktop",
    "finish-args": [
        "--device=dri",
        "--env=QTWEBENGINEPROCESS_PATH=/app/bin/QtWebEngineProcess",
        "--socket=wayland",
        "--socket=fallback-x11",
        "--socket=pulseaudio",
        "--share=network",
        "--share=ipc",
    ],
    "cleanup": [
        "/include",
        "/lib/pkgconfig",
        "/lib/cmake",
        "/lib/*.la",
        "/bin/curl",
        "/bin/copydatabase",
        "/bin/kiwix-compile-resources",
        "/bin/kiwix-manage",
        "/bin/kiwix-read",
        "/bin/kiwix-search",
        "/bin/quest",
        "/bin/simple*",
        "/bin/xapian-*",
        "/share/aclocal",
        "/share/doc",
        "/share/man",
    ],
    "cleanup-commands": ["/app/cleanup-BaseApp.sh"],
}

GET_REF_URL_API_TEMPLATE = "https://api.github.com/repos{repo}/git/refs/tags/{ref}"


class FlatpakBuilder:
    def __init__(self):
        self._targets = {}
        ConfigInfo.get_config("neutral", self._targets)
        self.config = ConfigInfo.get_config("flatpak", self._targets)
        if neutralEnv("distname") not in self.config.compatible_hosts:
            print(
                (
                    "ERROR: The config {} cannot be build on host {}.\n"
                    "Select another config or change your host system."
                ).format(self.config.name, neutralEnv("distname"))
            )
        self.targetDefs = self.config.add_targets(option("target"), self._targets)

    def finalize_target_steps(self):
        steps = []
        for targetDef in self.targetDefs:
            steps += self.order_steps(targetDef)
        steps = list(remove_duplicates(steps))

        for cfgName in ConfigInfo.all_running_configs:
            cfg = ConfigInfo.all_configs[cfgName]
            for tlcName in cfg.toolchain_names:
                tlc = Dependency.all_deps[tlcName]
                src_cfg_step = ("source", tlcName)
                add_target_step(src_cfg_step, self._targets[src_cfg_step])
                blt_cfg_step = ("neutral" if tlc.neutral else cfgName, tlcName)
                add_target_step(blt_cfg_step, self._targets[blt_cfg_step])

        for dep in steps:
            add_target_step(dep, self._targets[dep])
        self.instanciate_steps()

    def order_steps(self, targetDef):
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
            if isinstance(dep, tuple):
                depConfig, depName = dep
            else:
                depConfig, depName = targetConfigName, dep
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

    def configure(self):
        steps = remove_duplicates(target_steps())
        modules = OrderedDict()
        for stepDef in steps:
            module = modules.setdefault(stepDef[1], {})
            module["name"] = stepDef[1]
            if stepDef[0] == "source":
                source = get_target_step(stepDef)
                if getattr(source, "flatpak_no_autogen", False):
                    module["no-autogen"] = True
                module_sources = module.setdefault("sources", [])
                if isinstance(source, ReleaseDownload):
                    src = {
                        "type": "archive",
                        "sha256": source.archive.sha256,
                        "url": source.archive.url,
                    }
                    if hasattr(source, "flatpak_dest"):
                        src["dest"] = source.flatpak_dest
                    module_sources.append(src)
                elif isinstance(source, GitClone):
                    src = {
                        "type": "git",
                        "url": source.git_remote,
                        "tag": source.git_ref,
                    }
                    try:
                        parsed = urlparse(source.git_remote)
                        if parsed.hostname == "github.com":
                            repo = parsed.path[:-4]
                            api_url = GET_REF_URL_API_TEMPLATE.format(
                                repo=repo, ref=source.git_ref
                            )
                            with urlopen(api_url) as r:
                                ret = json.loads(r.read())
                            src["commit"] = ret["object"]["sha"]
                    except:
                        pass
                    module_sources.append(src)
                for p in getattr(source, "patches", []):
                    patch = {"type": "patch", "path": "patches/" + p}
                    module_sources.append(patch)

                if hasattr(source, "flatpak_command"):
                    command = {"type": "shell", "commands": [source.flatpak_command]}
                    module_sources.append(command)

            else:
                builder = get_target_step(stepDef)
                builder.set_flatpak_buildsystem(module)
                print(module["name"])

        manifest = MANIFEST.copy()
        modules = [m for m in modules.values() if m.get("sources")]
        for m in modules:
            temp = m["sources"]
            del m["sources"]
            m["sources"] = temp
        manifest["modules"] = modules
        manifest_name = "{}.json".format(MANIFEST["app-id"])
        manifest_path = pj(self.config.buildEnv.build_dir, manifest_name)
        with open(manifest_path, "w") as f:
            f.write(json.dumps(manifest, indent=4))

    def copy_patches(self):
        sourceDefs = (tDef for tDef in target_steps() if tDef[0] == "source")
        for sourceDef in sourceDefs:
            source = get_target_step(sourceDef)
            if not hasattr(source, "patches"):
                continue
            for p in source.patches:
                path = pj(SCRIPT_DIR, "patches", p)
                os.makedirs(
                    pj(self.config.buildEnv.build_dir, "patches"), exist_ok=True
                )
                dest = pj(self.config.buildEnv.build_dir, "patches", p)
                copyfile(path, dest)

    def build(self):
        log = pj(self.config.buildEnv.log_dir, "cmd_build_flatpak.log")
        context = Context("build", log, False)
        command = [
            "flatpak-builder",
            "--user",
            "--ccache",
            "--force-clean",
            "--keep-build-dirs",
            "--disable-rofiles-fuse",
            "--repo=repo",
            "builddir",
            f"{MANIFEST['app-id']}.json",
        ]
        try:
            run_command(
                command,
                self.config.buildEnv.build_dir,
                context,
                env=self.config.get_env(),
            )
            context._finalise()
        except subprocess.CalledProcessError:
            with open(log, "r") as f:
                print(f.read())
            raise StopBuild()

    def bundle(self):
        log = pj(self.config.buildEnv.log_dir, "cmd_bundle_flatpak.log")
        context = Context("bundle", log, False)
        app_id = MANIFEST["app-id"]
        command = ["flatpak", "build-bundle", "repo", f"{app_id}.flatpak", app_id]
        try:
            run_command(
                command,
                self.config.buildEnv.build_dir,
                context,
                env=self.config.get_env(),
            )
            context._finalise()
        except subprocess.CalledProcessError:
            with open(log, "r") as f:
                print(f.read())
            raise StopBuild()

    def _get_packages(self):
        package_name_mapper = PACKAGE_NAME_MAPPERS.get("flatpak", {})

        to_drop = []
        for builderDef in self._targets:
            configName, builderName = builderDef
            packages = package_name_mapper.get(builderName)
            if packages:
                to_drop.append(builderDef)
        for dep in to_drop:
            del self._targets[dep]

    def run(self):
        try:
            # This is a small hack, we don't need the list of packages to
            # install in a flatpak sdk, but _get_packages() will drop the
            # dependencies we already have in the sdk.
            self._get_packages()
            self.finalize_target_steps()
            print("[SETUP TOOLCHAINS]")
            for config in ConfigInfo.all_running_configs.values():
                config.finalize_setup()
            for cfgName in ConfigInfo.all_running_configs:
                cfg = ConfigInfo.all_configs[cfgName]
                for tlcName in cfg.toolchain_names:
                    tlc = Dependency.all_deps[tlcName]
                    builderDef = (cfgName, tlcName)
                    builder = get_target_step(builderDef)
                    print("build {} ({}):".format(builder.name, cfgName))
                    add_target_step(builderDef, builder)
                    builder.build()
            print("[GENERATE FLATPAK MANIFEST]")
            self.configure()
            self.copy_patches()
            print("[BUILD FLATBACK]")
            self.build()
            print("[BUNDLE]")
            self.bundle()
            # No error, clean intermediate file at end of build if needed.
            print("[CLEAN]")
            if option("clean_at_end"):
                for config in ConfigInfo.all_running_configs.values():
                    config.clean_intermediate_directories()
            else:
                print("SKIP")
        except StopBuild:
            sys.exit("Stopping build due to errors")
