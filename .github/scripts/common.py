import os
from os import environ as _environ
from pathlib import Path
from datetime import date
import tarfile
import subprocess
import re

from kiwixbuild.versions import base_deps_versions


PLATFORM_TARGET = _environ["PLATFORM_TARGET"]
OS_NAME = _environ["OS_NAME"]
HOME = Path(os.path.expanduser("~"))

BASE_DIR = HOME / "BUILD_{}".format(PLATFORM_TARGET)
SOURCE_DIR = HOME / "SOURCE"
ARCHIVE_DIR = HOME / "ARCHIVE"
INSTALL_DIR = BASE_DIR / "INSTALL"
TMP_DIR = Path("/tmp")

# [TODO]
KIWIX_DESKTOP_ONLY = False

_ref = _environ.get("GITHUB_REF", "").split("/")[-1]
MAKE_RELEASE = re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", _ref) is not None


def print_message(message, *args, **kwargs):
    message = message.format(*args, **kwargs)
    message = "{0} {1} {0}".format("-" * 3, message)
    print(message, flush=True)


MANIFEST_TEMPLATE = """{archive_name}
***************************

Dependencies archive for {target} on platform {platform}
Generated at {date}
"""


def write_manifest(manifest_file, archive_name, target, platform):
    with manifest_file.open(mode="w") as f:
        f.write(
            MANIFEST_TEMPLATE.format(
                archive_name=archive_name,
                target=target,
                platform=platform,
                date=date.today().isoformat(),
            )
        )


def run_kiwix_build(
    target,
    platform,
    build_deps_only=False,
    target_only=False,
    make_release=False,
    make_dist=False,
):
    command = ["kiwix-build"]
    command.append(target)
    command.append("--hide-progress")
    if platform == "flatpak" or platform.startswith("win32_"):
        command.append("--assume-packages-installed")
    if target == "kiwix-lib-app" and platform.startswith("android_"):
        command.extend(["--target-platform", "android", "--android-arch", platform[8:]])
    elif platform == "android":
        command.extend(["--target-platform", "android"])
        for arch in ("arm", "arm64", "x86", "x86_64"):
            command.extend(["--android-arch", arch])
    else:
        command.extend(["--target-platform", platform])
    if build_deps_only:
        command.append("--build-deps-only")
    if target_only:
        command.append("--build-nodeps")
    if make_release:
        command.append("--make-release")
    if make_dist:
        command.append("--make-dist")
    print_message(
        "Build {} (deps={}, release={}, dist={})",
        target,
        build_deps_only,
        make_release,
        make_dist,
    )
    env = dict(_environ)
    env['SKIP_BIG_MEMORY_TEST'] = '1'
    subprocess.check_call(command, cwd=str(HOME), env=env)
    print_message("Build ended")


def upload(file_to_upload, host, dest_path):
    command = [
        "scp",
        "-i",
        _environ.get("SSH_KEY"),
        "-o",
        "StrictHostKeyChecking=no",
        str(file_to_upload),
        "{}:{}".format(host, dest_path),
    ]
    print_message("Sending archive with command {}", command)
    subprocess.check_call(command)


def make_deps_archive(target=None, name=None, full=False):
    archive_name = name or "deps2_{}_{}_{}.tar.xz".format(
        OS_NAME, PLATFORM_TARGET, target
    )
    print_message("Create archive {}.", archive_name)
    files_to_archive = [INSTALL_DIR]
    files_to_archive += HOME.glob("BUILD_*/LOGS")
    if PLATFORM_TARGET == "native_mixed":
        files_to_archive += [HOME / "BUILD_native_static" / "INSTALL"]
    if PLATFORM_TARGET.startswith("android"):
        files_to_archive.append(HOME / "BUILD_neutral" / "INSTALL")
    if PLATFORM_TARGET == "android":
        for arch in ("arm", "arm64", "x86", "x86_64"):
            base_dir = HOME / "BUILD_android_{}".format(arch)
            files_to_archive.append(base_dir / "INSTALL")
            if (base_dir / "meson_cross_file.txt").exists():
                files_to_archive.append(base_dir / "meson_cross_file.txt")
    files_to_archive += HOME.glob("BUILD_*/android-ndk*")
    files_to_archive += HOME.glob("BUILD_*/android-sdk*")
    if (BASE_DIR / "meson_cross_file.txt").exists():
        files_to_archive.append(BASE_DIR / "meson_cross_file.txt")

    manifest_file = BASE_DIR / "manifest.txt"
    write_manifest(manifest_file, archive_name, target, PLATFORM_TARGET)
    files_to_archive.append(manifest_file)

    relative_path = HOME
    if full:
        files_to_archive += ARCHIVE_DIR.glob(".*_ok")
        files_to_archive += BASE_DIR.glob("*/.*_ok")
        files_to_archive += (HOME / "BUILD_native_dyn").glob("*/.*_ok")
        files_to_archive += (HOME / "BUILD_native_static").glob("*/.*_ok")
        files_to_archive += HOME.glob("BUILD_android*/**/.*_ok")
        files_to_archive += SOURCE_DIR.glob("*/.*_ok")
        files_to_archive += [
            SOURCE_DIR / "pugixml-{}".format(base_deps_versions["pugixml"])
        ]
        files_to_archive += HOME.glob(
            "BUILD_*/pugixml-{}".format(base_deps_versions["pugixml"])
        )
        if PLATFORM_TARGET.startswith("armhf"):
            files_to_archive += (SOURCE_DIR / "armhf").glob("*")
        toolchains_subdirs = HOME.glob("BUILD_*/TOOLCHAINS/*/*")
        for subdir in toolchains_subdirs:
            if not subdir.match("tools"):
                files_to_archive.append(subdir)

    archive_file = TMP_DIR / archive_name
    with tarfile.open(str(archive_file), "w:xz") as tar:
        for name in set(files_to_archive):
            print(".{}".format(name), flush=True)
            tar.add(str(name), arcname=str(name.relative_to(relative_path)))

    return archive_file
