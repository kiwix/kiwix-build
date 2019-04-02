#!/usr/bin/env python3

import sys, os
import shutil
from os import environ
from pathlib import Path
from datetime import date
import tarfile, zipfile
import subprocess
import re
from urllib.request import urlopen
from urllib.error import URLError

from kiwixbuild.versions import (
    main_project_versions,
    release_versions,
    base_deps_versions,
    base_deps_meta_version)

PLATFORM = environ['PLATFORM']
TRAVIS_OS_NAME = environ['TRAVIS_OS_NAME']
HOME = Path(os.path.expanduser('~'))
NIGHTLY_DATE = environ['NIGHTLY_DATE']
KBUILD_SOURCE_DIR = Path(environ['TRAVIS_BUILD_DIR'])
KIWIX_DESKTOP_ONLY = environ.get('DESKTOP_ONLY') == '1'

BASE_DIR = HOME/"BUILD_{}".format(PLATFORM)
SOURCE_DIR = HOME/"SOURCE"
ARCHIVE_DIR = HOME/"ARCHIVE"
INSTALL_DIR = BASE_DIR/"INSTALL"
NIGHTLY_KIWIX_ARCHIVES_DIR = HOME/'NIGHTLY_KIWIX_ARCHIVES'/NIGHTLY_DATE
RELEASE_KIWIX_ARCHIVES_DIR = HOME/'RELEASE_KIWIX_ARCHIVES'
NIGHTLY_ZIM_ARCHIVES_DIR = HOME/'NIGHTLY_ZIM_ARCHIVES'/NIGHTLY_DATE
RELEASE_ZIM_ARCHIVES_DIR = HOME/'RELEASE_ZIM_ARCHIVES'
DIST_KIWIX_ARCHIVES_DIR = HOME/'DIST_KIWIX_ARCHIVES'
DIST_ZIM_ARCHIVES_DIR = HOME/'DIST_ZIM_ARCHIVES'
SSH_KEY = KBUILD_SOURCE_DIR/'travis'/'travisci_builder_id_key'

BIN_EXT = '.exe' if PLATFORM.startswith('win32_') else ''

# We have build everything. Now create archives for public deployement.
EXPORT_FILES = {
    'kiwix-tools':
        (INSTALL_DIR/'bin', [f+BIN_EXT for f in ('kiwix-manage', 'kiwix-read', 'kiwix-search', 'kiwix-serve')]),
    'zim-tools':
        (INSTALL_DIR/'bin', [f+BIN_EXT for f in ('zimbench', 'zimcheck', 'zimdump', 'zimsearch', 'zimdiff', 'zimpatch', 'zimsplit')]),
    'zimwriterfs':
        (INSTALL_DIR/'bin', ['zimwriterfs'+BIN_EXT]),
    'libzim':
        (INSTALL_DIR, ('lib/x86_64-linux-gnu/libzim.so.{}'.format(main_project_versions['libzim']),
                       'lib/x86_64-linux-gnu/libzim.so.{}'.format(main_project_versions['libzim'][0]),
                       'include/zim/**/*.h'))
}

FLATPAK_GIT_REMOTE = 'git@github.com:flathub/org.kiwix.desktop.git'

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
    if platform == 'flatpak':
        command.append('--assume-packages-installed')
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


def create_desktop_image():
    if make_release:
        postfix = main_project_versions['kiwix-desktop']
        extra_postfix = release_versions.get('kiwix-desktop')
        if extra_postfix is None:
            # We should not make archives for release not wanted
            return
        if extra_postfix:
            postfix = "{}-{}".format(postfix, extra_postfix)
        archive_dir = RELEASE_KIWIX_ARCHIVES_DIR/'kiwix-desktop'
        src_dir = SOURCE_DIR/'kiwix-desktop_release'
    else:
        postfix = _date
        archive_dir = NIGHTLY_KIWIX_ARCHIVES_DIR
        src_dir = SOURCE_DIR/'kiwix-desktop'

    if PLATFORM == 'flatpak':
        build_path = BASE_DIR/'org.kiwix.desktop.flatpak'
        app_name = 'org.kiwix.desktop.{}.flatpak'.format(postfix)
    else:
        build_path = HOME/'Kiwix-{}-x86_64.AppImage'.format(postfix)
        app_name = "kiwix-desktop_x86_64_{}.appimage".format(postfix)
        command = ['kiwix-build/scripts/create_kiwix-desktop_appImage.sh',
                   str(INSTALL_DIR), str(src_dir), str(HOME/'AppDir')]
        env = dict(os.environ)
        env['VERSION'] = postfix
        print_message("Build AppImage of kiwix-desktop")
        subprocess.check_call(command, cwd=str(HOME), env=env)

    try:
        archive_dir.mkdir(parents=True)
    except FileExistsError:
        pass

    print_message("Copy Build to {}".format(archive_dir/app_name))
    shutil.copy(str(build_path), str(archive_dir/app_name))


def make_archive(project, platform):
    base_dir, export_files = EXPORT_FILES[project]

    if make_release:
        postfix = main_project_versions[project]
        extra_postfix = release_versions.get(project)
        if extra_postfix is None:
            # We should not make archives for release not wanted
            return
        if extra_postfix:
            postfix = "{}-{}".format(postfix, extra_postfix)
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

    files_to_archive = []
    for export_file in export_files:
        files_to_archive.extend(base_dir.glob(export_file))
    if platform == "win-i686":
        open_archive = lambda a : zipfile.ZipFile(str(a), 'w', compression=zipfile.ZIP_DEFLATED)
        archive_add = lambda a, f : a.write(str(f), arcname=str(f.relative_to(base_dir)))
        archive_ext = ".zip"
    else:
        open_archive = lambda a : tarfile.open(str(a), 'w:gz')
        archive_add = lambda a, f : a.add(str(f), arcname="{}/{}".format(archive_name, str(f.relative_to(base_dir))))
        archive_ext = ".tar.gz"


    archive = archive_dir/'{}{}'.format(archive_name, archive_ext)
    with open_archive(archive) as arch:
        for f in files_to_archive:
            archive_add(arch, f)


def make_deps_archive(target, full=False):
    archive_name = "deps_{}_{}_{}.tar.xz".format(
        TRAVIS_OS_NAME, PLATFORM, target)
    print_message("Create archive {}.", archive_name)
    files_to_archive = [INSTALL_DIR]
    files_to_archive += HOME.glob('BUILD_*/LOGS')
    if PLATFORM == 'native_mixed':
        files_to_archive += [HOME/'BUILD_native_static'/'INSTALL']
    if PLATFORM.startswith('android'):
        files_to_archive.append(HOME/'BUILD_neutral'/'INSTALL')
    if PLATFORM == 'android':
        for arch in ('arm', 'arm64', 'x86', 'x86_64'):
            base_dir = HOME/"BUILD_android_{}".format(arch)
            files_to_archive.append(base_dir/'INSTALL')
            if (base_dir/'meson_cross_file.txt').exists():
                files_to_archive.append(base_dir/'meson_cross_file.txt')
    files_to_archive += HOME.glob('BUILD_*/android-ndk*')
    files_to_archive += HOME.glob('BUILD_*/android-sdk*')
    if (BASE_DIR/'meson_cross_file.txt').exists():
        files_to_archive.append(BASE_DIR/'meson_cross_file.txt')

    manifest_file = BASE_DIR/'manifest.txt'
    write_manifest(manifest_file, archive_name, target, PLATFORM)
    files_to_archive.append(manifest_file)

    relative_path = HOME
    if full:
        files_to_archive += ARCHIVE_DIR.glob(".*_ok")
        files_to_archive += BASE_DIR.glob('*/.*_ok')
        files_to_archive += (HOME/"BUILD_native_dyn").glob('*/.*_ok')
        files_to_archive += (HOME/"BUILD_native_static").glob('*/.*_ok')
        files_to_archive += HOME.glob('BUILD_android*/**/.*_ok')
        files_to_archive += SOURCE_DIR.glob('*/.*_ok')
        files_to_archive += [SOURCE_DIR/'pugixml-{}'.format(
            base_deps_versions['pugixml'])]
        files_to_archive += HOME.glob('BUILD_*/pugixml-{}'.format(
            base_deps_versions['pugixml']))
        toolchains_subdirs = HOME.glob('**/TOOLCHAINS/*/*')
        if PLATFORM.startswith('armhf'):
            files_to_archive += [SOURCE_DIR/'raspberrypi-tools']
        for subdir in toolchains_subdirs:
            if not subdir.match('tools'):
                files_to_archive.append(subdir)

    with tarfile.open(str(relative_path/archive_name), 'w:xz') as tar:
        for name in set(files_to_archive):
            print('.', end='', flush=True)
            tar.add(str(name), arcname=str(name.relative_to(relative_path)))
    return relative_path/archive_name


def update_flathub_git():
    env = dict(os.environ)
    env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no -i {}'.format(SSH_KEY)
    env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = "KiwixBot"
    env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = "kiwixbot@kymeria.fr"
    command = ['git', 'clone', FLATPAK_GIT_REMOTE]
    subprocess.check_call(command, env=env, cwd=str(HOME))
    shutil.copy(str(BASE_DIR/'org.kiwix.desktop.json'),
                str(HOME/'org.kiwix.desktop'))
    patch_dir = KBUILD_SOURCE_DIR/'kiwixbuild'/'patches'
    for dep in ('libaria2', 'mustache', 'pugixml', 'xapian'):
        for f in patch_dir.glob('{}_*.patch'.format(dep)):
            shutil.copy(str(f), str(HOME/'org.kiwix.desktop'/'patches'))
    command = ['git', 'add', '-A', '.']
    subprocess.check_call(command, env=env, cwd=str(HOME/'org.kiwix.desktop'))
    command = ['git', 'commit', '-m',
               'Update to version {}'.format(main_project_versions['kiwix-desktop'])]
    subprocess.check_call(command, env=env, cwd=str(HOME/'org.kiwix.desktop'))
    command = ['git', 'push']
    subprocess.check_call(command, env=env, cwd=str(HOME/'org.kiwix.desktop'))



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

def download_base_archive(base_name):
    url = 'http://tmp.kiwix.org/ci/{}'.format(base_name)
    file_path = str(HOME/base_name)
    batch_size = 1024*1024*8
    with urlopen(url) as resource, open(file_path, 'wb') as file:
        while True:
            batch = resource.read(batch_size)
            if not batch:
                break
            print(".", end="", flush=True)
            file.write(batch)
    return file_path

if PLATFORM != 'flatpak':
    # The first thing we need to do is to (potentially) download already compiled base dependencies.
    base_dep_archive_name = "base_deps_{os}_{platform}_{version}_{release}.tar.xz".format(
        os=TRAVIS_OS_NAME,
        platform=PLATFORM,
        version=base_deps_meta_version,
        release='release' if make_release else 'debug')

    print_message("Getting archive {}", base_dep_archive_name)
    try:
        local_filename = download_base_archive(base_dep_archive_name)
        with tarfile.open(local_filename) as f:
            f.extractall(str(HOME))
    except URLError:
        print_message("Cannot get archive. Build dependencies")
        if PLATFORM == 'android':
            for arch in ('arm', 'arm64', 'x86', 'x86_64'):
                archive_name = "base_deps_{os}_android_{arch}_{version}_{release}.tar.xz".format(
                    os=TRAVIS_OS_NAME,
                    arch=arch,
                    version=base_deps_meta_version,
                    release='release' if make_release else 'debug')
                print_message("Getting archive {}", archive_name)
                try:
                    local_filename = download_base_archive(archive_name)
                    with tarfile.open(local_filename) as f:
                        f.extractall(str(HOME))
                except URLError:
                    pass
        run_kiwix_build('alldependencies', platform=PLATFORM)
        if SSH_KEY.exists():
            archive = make_deps_archive('alldependencies', full=True)
            destination = 'ci@tmp.kiwix.org:/data/tmp/ci/{}'
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
        elif PLATFORM == 'native_mixed':
            TARGETS = ('libzim', )
        else:
            TARGETS = ('kiwix-tools', 'zim-tools', 'zimwriterfs')
    elif PLATFORM == 'flatpak':
        TARGETS = ('kiwix-desktop', )
    else:
        TARGETS = ('kiwix-tools', )

    for target in TARGETS:
        run_kiwix_build(target,
                        platform=PLATFORM)

    if PLATFORM == 'native_mixed':
        make_archive('libzim', 'linux-x86_64')
    elif PLATFORM == 'native_static':
        for target in ('kiwix-tools', 'zim-tools', 'zimwriterfs'):
            make_archive(target, 'linux-x86_64')
    elif PLATFORM == 'win32_static':
        make_archive('kiwix-tools', 'win-i686')
    elif PLATFORM == 'armhf_static':
        make_archive('kiwix-tools', 'linux-armhf')
    elif PLATFORM == 'i586_static':
        make_archive('kiwix-tools', 'linux-i586')

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
            TARGETS = ('kiwix-desktop', )
        elif PLATFORM == 'native_mixed':
            TARGETS = ('libzim', )
        else:
            TARGETS = ('libzim', 'zimwriterfs', 'zim-tools', 'kiwix-lib', 'kiwix-tools')
elif PLATFORM == 'flatpak':
    TARGETS = ('kiwix-desktop', )
else:
    TARGETS = ('libzim', 'zim-tools', 'kiwix-lib', 'kiwix-tools')

for target in TARGETS:
    if environ['TRAVIS_EVENT_TYPE'] == 'cron' and PLATFORM not in ('android', 'flatpak'):
        run_kiwix_build(target,
                        platform=PLATFORM,
                        build_deps_only=True)
        archive = make_deps_archive(target)
        scp(archive, 'ci@tmp.kiwix.org:/data/tmp/ci/')

    run_kiwix_build(target,
                    platform=PLATFORM,
                    make_release=make_release)
    if target == 'kiwix-desktop':
        create_desktop_image()
    if make_release and PLATFORM == 'native_dyn' and release_versions.get(target) == 0:
        run_kiwix_build(target,
                        platform=PLATFORM,
                        make_release=True,
                        make_dist=True)

# We have build everything. Now create archives for public deployement.
if make_release and PLATFORM == 'native_dyn':
    for target in TARGETS:
        if release_versions.get(target) != 0:
            # Do not release project not in release_versions
            continue
        if target in ('kiwix-lib', 'kiwix-tools', 'kiwix-desktop'):
            out_dir = DIST_KIWIX_ARCHIVES_DIR
        else:
            out_dir = DIST_ZIM_ARCHIVES_DIR

        if target in ('kiwix-lib', 'kiwix-tools', 'libzim', 'zim-tools', 'zimwriterfs', 'kiwix-desktop'):
            try:
                (out_dir/target).mkdir(parents=True)
            except FileExistsError:
                pass

            full_target_name = "{}-{}".format(target, main_project_versions[target])
            if target != 'kiwix-desktop':
                in_file = BASE_DIR/full_target_name/'meson-dist'/'{}.tar.xz'.format(
                    full_target_name)
            else:
                in_file = BASE_DIR/full_target_name/'{}.tar.gz'.format(full_target_name)
            if in_file.exists():
                shutil.copy(str(in_file), str(out_dir/target))
elif PLATFORM == 'native_mixed':
    make_archive('libzim', 'linux-x86_64')
elif PLATFORM == 'native_static':
    for target in ('kiwix-tools', 'zim-tools', 'zimwriterfs'):
        make_archive(target, 'linux-x86_64')
elif PLATFORM == 'win32_static':
    make_archive('kiwix-tools', 'win-i686')
elif PLATFORM == 'armhf_static':
    make_archive('kiwix-tools', 'linux-armhf')
elif PLATFORM == 'i586_static':
    make_archive('kiwix-tools', 'linux-i586')
elif make_release and PLATFORM == 'flatpak':
    update_flathub_git()
elif PLATFORM.startswith('android') and 'kiwix-android' in TARGETS:
    APK_NAME = "kiwix-{}".format(PLATFORM)
    source_debug_dir = HOME/'BUILD_android'/'kiwix-android'/'app'/'build'/'outputs'/'apk'/'kiwix'/'debug'
    source_release_dir = HOME/'BUILD_android'/'kiwix-android'/'app'/'build'/'outputs'/'apk'/'kiwix'/'release'
    shutil.copy(str(source_debug_dir/'app-kiwix-debug.apk'),
                str(NIGHTLY_KIWIX_ARCHIVES_DIR/"{}-debug.apk".format(APK_NAME)))
    shutil.copy(str(source_release_dir/'app-kiwix-release-unsigned.apk'),
                str(NIGHTLY_KIWIX_ARCHIVES_DIR/"{}-release_signed".format(APK_NAME)))

