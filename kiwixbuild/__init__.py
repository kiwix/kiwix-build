#!/usr/bin/env python3

import os, sys
import argparse

from .dependencies import Dependency
from .platforms import PlatformInfo
from .builder import Builder
from . import _global

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', default='kiwix-tools', nargs='?', metavar='TARGET',
                        choices=Dependency.all_deps.keys())
    parser.add_argument('--working-dir', default=".")
    parser.add_argument('--libprefix', default=None)
    parser.add_argument('--target-platform', choices=PlatformInfo.all_platforms)
    parser.add_argument('--verbose', '-v', action="store_true",
                        help=("Print all logs on stdout instead of in specific"
                              " log files per commands"))
    parser.add_argument('--hide-progress', action='store_false', dest='show_progress',
                        help="Hide intermediate progress information.")
    parser.add_argument('--skip-source-prepare', action='store_true',
                        help="Skip the source download part")
    parser.add_argument('--build-deps-only', action='store_true',
                        help="Build only the dependencies of the specified target.")
    parser.add_argument('--build-nodeps', action='store_true',
                        help="Build only the target, not its dependencies.")
    parser.add_argument('--make-dist', action='store_true',
                        help="Build distrubution (dist) source archive")
    parser.add_argument('--make-release', action='store_true',
                        help="Build a release version")
    subgroup = parser.add_argument_group('advanced')
    subgroup.add_argument('--no-cert-check', action='store_true',
                          help="Skip SSL certificate verification during download")
    subgroup.add_argument('--clean-at-end', action='store_true',
                          help="Clean all intermediate files after the (successfull) build")
    subgroup.add_argument('--dont-install-packages', action='store_true',
                          help="Do not try to install packages before compiling")
    subgroup.add_argument('--android-arch', action='append',
                          help=("Specify the architecture to build for android application/libraries.\n"
                                "Can be specified several times to build for several architectures.\n"
                                "If not specified, all architectures will be build."))
    subgroup.add_argument('--ios-arch', action='append',
                          help=("Specify the architecture to build for ios application/libraries.\n"
                                "Can be specified several times to build for several architectures.\n"
                                "If not specified, all architectures will be build."))
    subgroup = parser.add_argument_group('custom app',
                                         description="Android custom app specific options")
    subgroup.add_argument('--android-custom-app',
                          help="The custom android app to build")
    subgroup.add_argument('--zim-file-url',
                          help="The url of the zim file to download")
    subgroup.add_argument('--zim-file-size',
                          help="The size of the zim file.")
    options = parser.parse_args()

    if options.target == 'kiwix-android-custom':
        err = False
        if not options.android_custom_app:
            print("You need to specify ANDROID_CUSTOM_APP if you "
                  "want to build a kiwix-android-custom target")
            err = True
        if not options.zim_file_url and not options.zim_file_size:
            print("You need to specify ZIM_FILE_SIZE or ZIM_FILE_URL if you "
                  "want to build a kiwix-android-custom target")
            err = True
        if err:
            sys.exit(1)
    if not options.android_arch:
        options.android_arch = ['arm', 'arm64', 'mips', 'mips64', 'x86', 'x86_64']
    if not options.ios_arch:
        options.ios_arch = ['armv7', 'arm64', 'i386', 'x86_64']

    if not options.target_platform:
        if options.target == 'kiwix-android':
             options.target_platform = 'android'
        else:
             options.target_platform = 'native_dyn'

    return options

def main():
    options = parse_args()
    options.working_dir = os.path.abspath(options.working_dir)
    _global.set_options(options)
    neutralEnv = buildenv.PlatformNeutralEnv()
    _global.set_neutralEnv(neutralEnv)
    builder = Builder()
    builder.run()

