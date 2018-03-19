#!/usr/bin/env python3

import sys, os
import shutil
from os import environ
from pathlib import Path
from datetime import date
import tarfile
import subprocess
import re

PLATFORM = environ['PLATFORM']

def home():
    return Path(os.path.expanduser('~'))

BASE_DIR = home()/"BUILD_{}".format(PLATFORM)
NIGHTLY_ARCHIVES_DIR = home()/'NIGHTLY_ARCHIVES'
RELEASE_KIWIX_ARCHIVES_DIR = home()/'RELEASE_KIWIX_ARCHIVES'
RELEASE_ZIM_ARCHIVES_DIR = home()/'RELEASE_ZIM_ARCHIVES'
DIST_KIWIX_ARCHIVES_DIR = home()/'DIST_KIWIX_ARCHIVES'
DIST_ZIM_ARCHIVES_DIR = home()/'DIST_ZIM_ARCHIVES'
SSH_KEY = Path(environ['TRAVIS_BUILD_DIR'])/'travis'/'travisci_builder_id_key'

VERSIONS = {
    'kiwix-lib': '1.0.2',
    'kiwix-tools': '0.3.0',
    'libzim': '3.0.0',
    'zim-tools': '0.0.1',
    'zimwriterfs': '1.1'
}

# We have build everything. Now create archives for public deployement.
BINARIES = {
    'kiwix-tools': ('kiwix-install', 'kiwix-manage', 'kiwix-read', 'kiwix-search', 'kiwix-serve'),
    'zim-tools': ('zimbench', 'zimdump', 'zimsearch', 'zimdiff', 'zimpatch', 'zimsplit'),
    'zimwriterfs': ('zimwriterfs',)
}

_date = date.today().isoformat()



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


def run_kiwix_build(target, platform, build_deps_only=False, make_release=False, make_dist=False):
    command = [str(Path(environ['TRAVIS_BUILD_DIR'])/'kiwix-build.py')]
    command.append(target)
    command.append('--hide-progress')
    command.extend(['--target-platform', platform])
    if build_deps_only:
        command.append('--build-deps-only')
    if make_release:
        command.append('--make-release')
    if make_dist:
        command.append('--make-dist')
    subprocess.check_call(command, cwd=str(home()))


def make_archive(project, platform):
    file_to_archives = BINARIES[project]
    if platform == "win32":
        file_to_archives = ['{}.exe'.format(f) for f in file_to_archives]
    if make_release:
        postfix = VERSIONS[project]
        if project in ('kiwix-lib', 'kiwix-tools'):
            archive_dir = RELEASE_KIWIX_ARCHIVES_DIR/project
        else:
            archive_dir = RELEASE_ZIM_ARCHIVES_DIR/project
    else:
        postfix = _date
        archive_dir = NIGHTLY_ARCHIVES_DIR
    archive_name = "{}_{}-{}".format(project, platform, postfix)
    archive = archive_dir/'{}.tar.gz'.format(archive_name)
    try:
        archive_dir.mkdir(parents=True)
    except FileExistsError:
        pass
    base_bin_dir = BASE_DIR/'INSTALL'/'bin'
    with tarfile.open(str(archive), 'w:gz') as arch:
        for f in file_to_archives:
            arch.add(str(base_bin_dir/f), arcname=str(f))


def scp(what, where):
    command = ['scp', '-i', str(SSH_KEY), what, where]
    subprocess.check_call(command)


for p in (NIGHTLY_ARCHIVES_DIR,
          RELEASE_KIWIX_ARCHIVES_DIR,
          RELEASE_ZIM_ARCHIVES_DIR,
          DIST_KIWIX_ARCHIVES_DIR,
          DIST_ZIM_ARCHIVES_DIR):
    try:
        p.mkdir(parents=True)
    except FileExistsError:
        pass

make_release = re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", environ.get('TRAVIS_TAG', '')) is not None

# A basic compilation to be sure everything is working (for a PR)
if environ['TRAVIS_EVENT_TYPE'] != 'cron' and not make_release:
    if PLATFORM.startswith('android'):
        TARGETS = ('kiwix-android',)
    elif PLATFORM.startswith('native_'):
        TARGETS = ('kiwix-tools', 'zim-tools', 'zimwriterfs')
    else:
        TARGETS = ('kiwix-tools', )

    for target in TARGETS:
        run_kiwix_build(target,
                        platform=PLATFORM)

    sys.exit(0)

if PLATFORM.startswith('android'):
    if make_release:
        # (For now ?) kiwix-android follow it own release process.
        # Do not try to make a release of it
        TARGETS = ('libzim', 'kiwix-lib')
    else:
        TARGETS = ('libzim', 'kiwix-lib', 'kiwix-android')
elif PLATFORM.startswith('native_'):
    TARGETS = ('libzim', 'zimwriterfs', 'zim-tools', 'kiwix-lib', 'kiwix-tools')
else:
    TARGETS = ('libzim', 'kiwix-lib', 'kiwix-tools')

for target in TARGETS:
    if environ['TRAVIS_EVENT_TYPE'] == 'cron':
        run_kiwix_build(target,
                        platform=PLATFORM,
                        build_deps_only=True)
        (BASE_DIR/'.install_packages_ok').unlink()

        archive_name = "deps_{}_{}.tar.gz".format(PLATFORM, target)
        files_to_archive = [BASE_DIR/'INSTALL']
        files_to_archive += BASE_DIR.glob('**/android-ndk*')
        if (BASE_DIR/'meson_cross_file.txt').exists():
            files_to_archive.append(BASE_DIR/'meson_cross_file.txt')

        manifest_file = BASE_DIR/'manifest.txt'
        write_manifest(manifest_file, archive_name, target, PLATFORM)
        files_to_archive.append(manifest_file)
        with tarfile.open(str(BASE_DIR/archive_name), 'w:gz') as tar:
            for name in files_to_archive:
                tar.add(str(name), arcname=str(name.relative_to(BASE_DIR)))
        scp(str(BASE_DIR/archive_name), 'nightlybot@download.kiwix.org:/var/www/tmp.kiwix.org/ci/')

    run_kiwix_build(target,
                    platform=PLATFORM,
                    make_release=make_release)
    if make_release and PLATFORM == 'native_dyn':
        run_kiwix_build(target,
                        platform=PLATFORM,
                        make_release=True,
                        make_dist=True)
    (BASE_DIR/'.install_packages_ok').unlink()


# We have build everything. Now create archives for public deployement.
kiwix_tools_postfix = VERSIONS['kiwix-tools'] if make_release else _date
zim_tools_postfix = VERSIONS['zim-tools'] if make_release else _date
zimwriterfs_postfix = VERSIONS['zimwriterfs'] if make_release else _date

if make_release and PLATFORM == 'native_dyn':
    for target in TARGETS:
        if target in ('kiwix-lib', 'kiwix-tools'):
            out_dir = DIST_KIWIX_ARCHIVES_DIR
        else:
            out_dir = DIST_ZIM_ARCHIVES_DIR

        if target in ('kiwix-lib', 'kiwix-tools', 'libzim', 'zim-tools'):
            shutil.copy(str(BASE_DIR/target/'meson-dist'/'{}-{}.tar.xz'.format(target, VERSIONS[target])),
                        str(out_dir))
        if target in ('zimwriterfs',):
            shutil.copy(str(BASE_DIR/target/'{}-{}.tar.gz'.format(target, VERSIONS[target])),
                        str(out_dir))
elif PLATFORM == 'native_static':
    for target in ('kiwix-tools', 'zim-tools', 'zimwriterfs'):
        make_archive(target, 'linux64')
elif PLATFORM == 'win32_static':
    make_archive('kiwix-tools', 'win32')
elif PLATFORM == 'armhf_static':
    make_archive('kiwix-tools', 'armhf')
elif PLATFORM.startswith('android_') and 'kiwix-android' in TARGETS:
    APK_NAME = "kiwix-{}".format(PLATFORM)
    source_debug_dir = BASE_DIR/'kiwix-android'/'app'/'build'/'outputs'/'apk'/'kiwix'/'debug'
    source_release_dir = BASE_DIR/'kiwix-android'/'app'/'build'/'outputs'/'apk'/'kiwix'/'release'
    shutil.copy(str(source_debug_dir/'app-kiwix-debug.apk'),
                str(NIGHTLY_ARCHIVES_DIR/"{}-debug.apk".format(APK_NAME)))
    shutil.copy(str(source_release_dir/'app-kiwix-release-unsigned.apk'),
                str(NIGHTLY_ARCHIVES_DIR/"{}-release_signed".format(APK_NAME)))

