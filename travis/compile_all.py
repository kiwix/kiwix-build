#!/usr/bin/env python3

import sys, os
import shutil
from os import environ
from pathlib import Path
from datetime import date
import tarfile, zipfile
import subprocess
import re
from urllib.request import urlretrieve
from urllib.error import URLError

from kiwixbuild.versions import (
    main_project_versions,
    base_deps_versions,
    base_deps_meta_version)

PLATFORM = environ['PLATFORM']
TRAVIS_OS_NAME = environ['TRAVIS_OS_NAME']
HOME = Path(os.path.expanduser('~'))
NIGHTLY_DATE = environ['NIGHTLY_DATE']
KIWIX_DESKTOP_ONLY = environ.get('DESKTOP_ONLY') == '1'

BASE_DIR = HOME/"BUILD_{}".format(PLATFORM)
SOURCE_DIR = HOME/"SOURCE"
ARCHIVE_DIR = HOME/"ARCHIVE"
TOOLCHAINS_DIR = HOME/"TOOLCHAINS"
NIGHTLY_KIWIX_ARCHIVES_DIR = HOME/'NIGHTLY_KIWIX_ARCHIVES'/NIGHTLY_DATE
RELEASE_KIWIX_ARCHIVES_DIR = HOME/'RELEASE_KIWIX_ARCHIVES'
NIGHTLY_ZIM_ARCHIVES_DIR = HOME/'NIGHTLY_ZIM_ARCHIVES'/NIGHTLY_DATE
RELEASE_ZIM_ARCHIVES_DIR = HOME/'RELEASE_ZIM_ARCHIVES'
DIST_KIWIX_ARCHIVES_DIR = HOME/'DIST_KIWIX_ARCHIVES'
DIST_ZIM_ARCHIVES_DIR = HOME/'DIST_ZIM_ARCHIVES'
SSH_KEY = environ.get('TRAVISCI_SSH_KEY', Path(environ['TRAVIS_BUILD_DIR'])/'travis'/'travisci_builder_id_key')

# We have build everything. Now create archives for public deployement.
BINARIES = {
    'kiwix-tools': ('kiwix-manage', 'kiwix-read', 'kiwix-search', 'kiwix-serve'),
    'zim-tools': ('zimbench', 'zimdump', 'zimsearch', 'zimdiff', 'zimpatch', 'zimsplit'),
    'zimwriterfs': ('zimwriterfs',)
}

_date = date.today().isoformat()

def print_message(message, *args, **kwargs):
    message = message.format(*args, **kwargs)
    message = "{0} {1} {0}".format('-'*3, message)
    print(message, flush=True)


def write_manifest(manifest_file, archive_name, target, platform):
    with manifest_file.open(mode='w') as f:
        f.write('''{archive_name}
***************************

Dependencies archive for {target} on platform {platform}
Generated at {date}
'''.format(
    archive_name=archive_name,
    target=target,
    platform=platform,
    date=date.today().isoformat()))


def run_kiwix_build(target, platform,
                    build_deps_only=False,
                    target_only=False,
                    make_release=False,
                    make_dist=False):
    command = ['kiwix-build']
    command.append(target)
    command.append('--hide-progress')
    if target == 'kiwix-android' and platform.startswith('android_'):
        command.extend(['--target-platform', 'android', '--android-arch', platform[8:]])
    elif platform == 'android':
        command.extend(['--target-platform', 'android'])
        for arch in ('arm', 'arm64', 'x86', 'x86_64'):
            command.extend(['--android-arch', arch])
    else:
        command.extend(['--target-platform', platform])
    if build_deps_only:
        command.append('--build-deps-only')
    if target_only:
        command.append('--build-nodeps')
    if make_release:
        command.append('--make-release')
    if make_dist:
        command.append('--make-dist')
    print_message("Build {} (deps={}, release={}, dist={})",
        target, build_deps_only, make_release, make_dist)
    subprocess.check_call(command, cwd=str(HOME))


def create_app_image():
    command = ['kiwix-build/scripts/create_kiwix-desktop_appImage.sh',
               str(BASE_DIR/'INSTALL'), str(HOME/'AppDir')]
    print_message("Build AppImage of kiwix-desktop")
    subprocess.check_call(command, cwd=str(HOME))
    if make_release:
        postfix = main_project_versions['kiwix-desktop']
        archive_dir = RELEASE_KIWIX_ARCHIVES_DIR/'kiwix-desktop'
    else:
        postfix = _date
        archive_dir = NIGHTLY_KIWIX_ARCHIVES_DIR

    try:
        archive_dir.mkdir(parents=True)
    except FileExistsError:
        pass

    app_name = "kiwix-desktop_x86_64_{}".format(postfix)
    print_message("Copy AppImage to {}".format(archive_dir/app_name))
    shutil.copy(str(HOME/'Kiwix-x86_64.AppImage'), str(archive_dir/app_name))


def make_archive(project, platform):
    file_to_archives = BINARIES[project]
    base_bin_dir = BASE_DIR/'INSTALL'/'bin'

    if make_release:
        postfix = main_project_versions[project]
        if project in ('kiwix-lib', 'kiwix-tools'):
            archive_dir = RELEASE_KIWIX_ARCHIVES_DIR/project
        else:
            archive_dir = RELEASE_ZIM_ARCHIVES_DIR/project
    else:
        postfix = _date
        if project in ('kiwix-lib', 'kiwix-tools'):
            archive_dir = NIGHTLY_KIWIX_ARCHIVES_DIR
        else:
            archive_dir = NIGHTLY_ZIM_ARCHIVES_DIR

    try:
        archive_dir.mkdir(parents=True)
    except FileExistsError:
        pass

    archive_name = "{}_{}-{}".format(project, platform, postfix)

    if platform == "win-i686":
        file_to_archives = ['{}.exe'.format(f) for f in file_to_archives]
        open_archive = lambda a : zipfile.ZipFile(str(a), 'w', compression=zipfile.ZIP_LZMA)
        archive_add = lambda a, f : a.write(str(base_bin_dir/f), arcname=str(f))
        archive_ext = ".zip"
    else:
        open_archive = lambda a : tarfile.open(str(a), 'w:gz')
        archive_add = lambda a, f : a.add(str(base_bin_dir/f), arcname="{}/{}".format(archive_name, str(f)))
        archive_ext = ".tar.gz"


    archive = archive_dir/'{}{}'.format(archive_name, archive_ext)
    with open_archive(archive) as arch:
        for f in file_to_archives:
            archive_add(arch, f)


def make_deps_archive(target, full=False):
    archive_name = "deps_{}_{}_{}.tar.gz".format(
        TRAVIS_OS_NAME, PLATFORM, target)
    files_to_archive = [BASE_DIR/'INSTALL']
    files_to_archive += HOME.glob('BUILD_*/android-ndk*')
    files_to_archive += HOME.glob('BUILD_*/android-sdk*')
    if (BASE_DIR/'meson_cross_file.txt').exists():
        files_to_archive.append(BASE_DIR/'meson_cross_file.txt')

    manifest_file = BASE_DIR/'manifest.txt'
    write_manifest(manifest_file, archive_name, target, PLATFORM)
    files_to_archive.append(manifest_file)

    relative_path = BASE_DIR
    if full:
        files_to_archive += ARCHIVE_DIR.glob(".*_ok")
        files_to_archive += BASE_DIR.glob('*/.*_ok')
        files_to_archive += (HOME/"BUILD_native_dyn").glob('*/.*_ok')
        files_to_archive += (HOME/"BUILD_native_static").glob('*/.*_ok')
        files_to_archive += HOME.glob('BUILD_android*/.*_ok')
        files_to_archive += SOURCE_DIR.glob('*/.*_ok')
        files_to_archive += [SOURCE_DIR/'pugixml-{}'.format(
            base_deps_versions['pugixml'])]
        files_to_archive += HOME.glob('BUILD_*/pugixml-{}'.format(
            base_deps_versions['pugixml']))
        files_to_archive += HOME.glob('**/TOOLCHAINS')
        relative_path = HOME

    with tarfile.open(str(relative_path/archive_name), 'w:gz') as tar:
        for name in set(files_to_archive):
            tar.add(str(name), arcname=str(name.relative_to(relative_path)))
    return relative_path/archive_name


def scp(what, where):
    print_message("Copy {} to {}", what, where)
    command = ['scp', '-o', 'StrictHostKeyChecking=no',
                      '-i', str(SSH_KEY),
                      str(what), str(where)]
    subprocess.check_call(command)


for p in (NIGHTLY_KIWIX_ARCHIVES_DIR,
          NIGHTLY_ZIM_ARCHIVES_DIR,
          RELEASE_KIWIX_ARCHIVES_DIR,
          RELEASE_ZIM_ARCHIVES_DIR,
          DIST_KIWIX_ARCHIVES_DIR,
          DIST_ZIM_ARCHIVES_DIR):
    try:
        p.mkdir(parents=True)
    except FileExistsError:
        pass

make_release = re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", environ.get('TRAVIS_TAG', '')) is not None

# The first thing we need to do is to (potentially) download already compiled base dependencies.
base_dep_archive_name = "base_deps_{os}_{platform}_{version}.tar.gz".format(
    os=TRAVIS_OS_NAME,
    platform=PLATFORM,
    version=base_deps_meta_version)

print_message("Getting archive {}", base_dep_archive_name)
try:
    local_filename, headers = urlretrieve(
        'http://tmp.kiwix.org/ci/{}'.format(base_dep_archive_name))
    with tarfile.open(local_filename) as f:
        f.extractall(str(HOME))
except URLError:
    print_message("Cannot get archive. Build dependencies")
    run_kiwix_build('alldependencies', platform=PLATFORM)
    archive = make_deps_archive('alldependencies', full=True)
    destination = 'nightlybot@download.kiwix.org:/var/www/tmp.kiwix.org/ci/{}'
    destination = destination.format(base_dep_archive_name)
    scp(archive, destination)




# A basic compilation to be sure everything is working (for a PR)
if environ['TRAVIS_EVENT_TYPE'] != 'cron' and not make_release:
    if PLATFORM.startswith('android'):
        TARGETS = ('kiwix-android',)
    elif PLATFORM.startswith('iOS'):
        TARGETS = ('kiwix-lib',)
    elif PLATFORM.startswith('native_'):
        if TRAVIS_OS_NAME == "osx":
            TARGETS = ('kiwix-lib', 'zim-tools', 'zimwriterfs')
        elif PLATFORM == 'native_dyn' and KIWIX_DESKTOP_ONLY:
            TARGETS = ('kiwix-desktop', )
        else:
            TARGETS = ('kiwix-tools', 'zim-tools', 'zimwriterfs')
    else:
        TARGETS = ('kiwix-tools', )

    for target in TARGETS:
        run_kiwix_build(target,
                        platform=PLATFORM)

    sys.exit(0)


TARGETS = tuple()
if PLATFORM.startswith('android'):
    if make_release:
        # (For now ?) kiwix-android follow it own release process.
        # Do not try to make a release of it
        TARGETS = ('libzim', 'kiwix-lib')
    else:
        TARGETS = ('libzim', 'kiwix-lib', 'kiwix-android')
elif PLATFORM.startswith('iOS'):
    TARGETS = ('libzim', 'kiwix-lib')
elif PLATFORM.startswith('native_'):
    if TRAVIS_OS_NAME == "osx":
        TARGETS = ('libzim', 'zimwriterfs', 'zim-tools', 'kiwix-lib')
    else:
        if PLATFORM == 'native_dyn' and KIWIX_DESKTOP_ONLY:
            if not make_release:
                TARGETS = ('kiwix-desktop', )
        else:
            TARGETS = ('libzim', 'kiwix-lib', 'kiwix-desktop', 'zimwriterfs', 'zim-tools', 'kiwix-tools')
else:
    TARGETS = ('libzim', 'zim-tools', 'kiwix-lib', 'kiwix-tools')

for target in TARGETS:
    if environ['TRAVIS_EVENT_TYPE'] == 'cron':
        run_kiwix_build(target,
                        platform=PLATFORM,
                        build_deps_only=True)
        archive = make_deps_archive(target)
        scp(archive, 'nightlybot@download.kiwix.org:/var/www/tmp.kiwix.org/ci/')

    run_kiwix_build(target,
                    platform=PLATFORM,
                    make_release=make_release,
                    target_only=True)
    if target == 'kiwix-desktop':
        create_app_image()
    if make_release and PLATFORM == 'native_dyn':
        run_kiwix_build(target,
                        platform=PLATFORM,
                        make_release=True,
                        make_dist=True)


# We have build everything. Now create archives for public deployement.
if make_release and PLATFORM == 'native_dyn':
    for target in TARGETS:
        if target in ('kiwix-lib', 'kiwix-tools'):
            out_dir = DIST_KIWIX_ARCHIVES_DIR
        else:
            out_dir = DIST_ZIM_ARCHIVES_DIR

        if target in ('kiwix-lib', 'kiwix-tools', 'libzim', 'zim-tools', 'zimwriterfs'):
            try:
                (out_dir/target).mkdir(parents=True)
            except FileExistsError:
                pass

            if target == 'zimwriterfs':
                in_file = BASE_DIR/target/'{}-{}.tar.gz'.format(
                    target,
                    main_project_versions[target])
            else:
                in_file = BASE_DIR/target/'meson-dist'/'{}-{}.tar.xz'.format(
                    target,
                    main_project_versions[target])

            shutil.copy(str(in_file), str(out_dir/target))
elif PLATFORM == 'native_static':
    for target in ('kiwix-tools', 'zim-tools', 'zimwriterfs'):
        make_archive(target, 'linux-x86_64')
elif PLATFORM == 'win32_static':
    make_archive('kiwix-tools', 'win-i686')
elif PLATFORM == 'armhf_static':
    make_archive('kiwix-tools', 'linux-armhf')
elif PLATFORM == 'i586_static':
    make_archive('kiwix-tools', 'linux-i586')
elif PLATFORM.startswith('android') and 'kiwix-android' in TARGETS:
    APK_NAME = "kiwix-{}".format(PLATFORM)
    source_debug_dir = HOME/'BUILD_android'/'kiwix-android'/'app'/'build'/'outputs'/'apk'/'kiwix'/'debug'
    source_release_dir = HOME/'BUILD_android'/'kiwix-android'/'app'/'build'/'outputs'/'apk'/'kiwix'/'release'
    shutil.copy(str(source_debug_dir/'app-kiwix-debug.apk'),
                str(NIGHTLY_KIWIX_ARCHIVES_DIR/"{}-debug.apk".format(APK_NAME)))
    shutil.copy(str(source_release_dir/'app-kiwix-release-unsigned.apk'),
                str(NIGHTLY_KIWIX_ARCHIVES_DIR/"{}-release_signed".format(APK_NAME)))

