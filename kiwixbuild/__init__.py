#!/usr/bin/env python3

import os, sys
import argparse
from pathlib import Path

from .dependencies import Dependency
from .configs import ConfigInfo
from .builder import Builder
from .flatpak_builder import FlatpakBuilder
from . import _global


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target",
        default="kiwix-tools",
        nargs="?",
        metavar="TARGET",
        choices=Dependency.all_deps.keys(),
    )
    parser.add_argument(
        "--working-dir",
        default=".",
        type=Path,
        help=(
            "Directory where kiwix-build puts all its files "
            "(source, archive and build)\n"
            "working-dir can be absolute path or a relative (to cwd) one."
        ),
    )
    parser.add_argument(
        "--build-dir",
        default=".",
        type=Path,
        help=(
            "Directory where kiwix-build puts all build files.\n"
            "build-dir can be absolute path or a relative (to working-dir) one."
        ),
    )
    parser.add_argument("--libprefix", default=None)
    parser.add_argument(
        "--config", choices=ConfigInfo.all_configs, default="native_dyn"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help=(
            "Print all logs on stdout instead of in specific" " log files per commands"
        ),
    )
    parser.add_argument(
        "--hide-progress",
        action="store_false",
        dest="show_progress",
        help="Hide intermediate progress information.",
    )
    parser.add_argument(
        "--skip-source-prepare",
        action="store_true",
        help="Skip the source download part",
    )
    parser.add_argument(
        "--build-deps-only",
        action="store_true",
        help="Build only the dependencies of the specified target.",
    )
    parser.add_argument(
        "--build-nodeps",
        action="store_true",
        help="Build only the target, not its dependencies.",
    )
    parser.add_argument(
        "--make-dist",
        action="store_true",
        help="Build distrubution (dist) source archive",
    )
    parser.add_argument(
        "--make-release", action="store_true", help="Build a release version"
    )
    subgroup = parser.add_argument_group("advanced")
    subgroup.add_argument(
        "--no-cert-check",
        action="store_true",
        help="Skip SSL certificate verification during download",
    )
    subgroup.add_argument(
        "--clean-at-end",
        action="store_true",
        help="Clean all intermediate files after the (successfull) build",
    )
    subgroup.add_argument(
        "--dont-install-packages",
        action="store_true",
        help="Do not try to install packages before compiling",
    )
    subgroup.add_argument(
        "--assume-packages-installed",
        action="store_true",
        help="Assume the package to install to be aleady installed",
    )
    subgroup.add_argument(
        "--android-arch",
        action="append",
        help=(
            "Specify the architecture to build for android application/libraries.\n"
            "Can be specified several times to build for several architectures.\n"
            "If not specified, all architectures will be build."
        ),
    )
    subgroup.add_argument(
        "--ios-arch",
        action="append",
        help=(
            "Specify the architecture to build for ios application/libraries.\n"
            "Can be specified several times to build for several architectures.\n"
            "If not specified, all architectures will be build."
        ),
    )
    subgroup.add_argument(
        "--fast-clone",
        action="store_true",
        help=(
            "Do not clone the whole repository.\n"
            "This is useful for one shot build but it is not recommended if you want "
            "to develop with the cloned sources."
        ),
    )
    subgroup.add_argument(
        "--use-target-arch-name",
        action="store_true",
        help=(
            "Name the build directory using the arch name instead of the config name.\n"
            "Different configs may create binary for the same arch so this option is "
            "not recommended when working with several config on the same computer.\n"
            "However, when generating dependencies for other it is better to have a "
            "directory named using the target instead of the used config.\n"
            "Intended to be used in CI only."
        ),
    )
    subgroup.add_argument(
        "--get-build-dir", action="store_true", help="Print the output directory."
    )
    options = parser.parse_args()

    if not options.android_arch:
        options.android_arch = ["arm", "arm64", "x86", "x86_64"]
    if not options.ios_arch:
        options.ios_arch = ["arm64", "x86_64"]

    return options


def main():
    options = parse_args()
    options.working_dir = options.working_dir.absolute()
    _global.set_options(options)
    neutralEnv = buildenv.NeutralEnv(options.get_build_dir)
    _global.set_neutralEnv(neutralEnv)
    if options.config == "flatpak":
        builder = FlatpakBuilder()
    else:
        builder = Builder()
    if options.get_build_dir:
        print(ConfigInfo.get_config(options.config).buildEnv.build_dir)
    else:
        builder.run()
