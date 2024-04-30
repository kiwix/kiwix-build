import os
from os import environ as _environ
from pathlib import Path, PurePosixPath
from datetime import date
import tarfile
import zipfile
import subprocess
import re
import shutil
import platform

import requests

from build_definition import get_platform_name, get_dependency_archive_name

from kiwixbuild.dependencies.apple_xcframework import AppleXCFramework
from kiwixbuild.versions import (
    main_project_versions,
    release_versions,
    base_deps_versions,
)


def get_build_dir(config) -> Path:
    command = ["kiwix-build"]
    command.extend(["--config", config])
    command.append("--get-build-dir")
    command.append("--use-target-arch-name")
    return Path(
        subprocess.run(command, cwd=str(HOME), check=True, stdout=subprocess.PIPE)
        .stdout.strip()
        .decode("utf8")
    )


COMPILE_CONFIG = _environ["COMPILE_CONFIG"]
OS_NAME = _environ["OS_NAME"]
HOME = Path(os.path.expanduser("~"))

BASE_DIR = get_build_dir(COMPILE_CONFIG)
SOURCE_DIR = HOME / "SOURCE"
ARCHIVE_DIR = HOME / "ARCHIVE"
TOOLCHAIN_DIR = BASE_DIR / "TOOLCHAINS"
INSTALL_DIR = BASE_DIR / "INSTALL"
default_tmp_dir = os.getenv("TEMP") if platform.system() == "Windows" else "/tmp"
TMP_DIR = Path(os.getenv("TMP_DIR", default_tmp_dir))
KBUILD_SOURCE_DIR = HOME / "kiwix-build"

_ref = _environ.get("GITHUB_REF", "").split("/")[-1]
MAKE_RELEASE = re.fullmatch(r"r_[0-9]+", _ref) is not None
MAKE_RELEASE = MAKE_RELEASE and (_environ.get("GITHUB_EVENT_NAME") != "schedule")

if not MAKE_RELEASE and _ref != "main":
    DEV_BRANCH = _ref
else:
    DEV_BRANCH = None

FLATPAK_HTTP_GIT_REMOTE = "https://github.com/flathub/org.kiwix.desktop.git"
FLATPAK_GIT_REMOTE = "git@github.com:flathub/org.kiwix.desktop.git"

BIN_EXT = ".exe" if COMPILE_CONFIG.startswith("win32_") else ""


def major_version(version: str) -> str:
    return version.split(".")[0]


# We have build everything. Now create archives for public deployement.
EXPORT_FILES = {
    "kiwix-tools": (
        INSTALL_DIR / "bin",
        [f + BIN_EXT for f in ("kiwix-manage", "kiwix-search", "kiwix-serve")],
    ),
    "zim-tools": (
        INSTALL_DIR / "bin",
        [
            f + BIN_EXT
            for f in (
                "zimbench",
                "zimcheck",
                "zimdump",
                "zimsearch",
                "zimdiff",
                "zimpatch",
                "zimsplit",
                "zimwriterfs",
                "zimrecreate",
            )
        ],
    ),
    "libzim": (
        INSTALL_DIR,
        (
            # We need to package all dependencies (`*.a`) on wasm
            "lib/*/libzim.a" if COMPILE_CONFIG != "wasm" else "lib/*.a",
            "lib/*/libzim.so",
            "lib/*/libzim.so.{version}".format(version=main_project_versions["libzim"]),
            "lib/*/libzim.so.{version}".format(
                version=major_version(main_project_versions["libzim"])
            ),
            "lib/libzim.{}.dylib".format(
                major_version(main_project_versions["libzim"])
            ),
            "lib/libzim.dylib",
            "lib/*/libzim.pc",
            "include/zim/**/*.h",
            "share/icu/{}/icudt{}l.dat".format(
                base_deps_versions["icu4c"], major_version(base_deps_versions["icu4c"])
            ),
        ),
    ),
    "libkiwix": (
        INSTALL_DIR,
        (
            "lib/CoreKiwix.xcframework/",
            "lib/*/libkiwix.so",
            "lib/*/libkiwix.so.{version}".format(
                version=main_project_versions["libkiwix"]
            ),
            "lib/*/libkiwix.so.{version}".format(
                version=major_version(main_project_versions["libkiwix"])
            ),
            "lib/libkiwix.{}.dylib".format(
                major_version(main_project_versions["libkiwix"])
            ),
            "lib/libkiwix.dylib",
            "lib/*/libkiwix.pc",
            "include/kiwix/**/*.h",
            "share/icu/{}/icudt{}l.dat".format(
                base_deps_versions["icu4c"], major_version(base_deps_versions["icu4c"])
            ),
        ),
    ),
}

DATE = date.today().isoformat()


def print_message(message, *args, **kwargs):
    message = message.format(*args, **kwargs)
    message = "{0} {1} {0}".format("-" * 3, message)
    print(message, flush=True)


MANIFEST_TEMPLATE = """{archive_name}
***************************

Dependencies archive for {target} using config {config}
Generated at {date}
"""


def write_manifest(manifest_file, archive_name, target, config):
    with manifest_file.open(mode="w") as f:
        f.write(
            MANIFEST_TEMPLATE.format(
                archive_name=archive_name,
                target=target,
                config=config,
                date=DATE,
            )
        )


def run_kiwix_build(
    target,
    config,
    build_deps_only=False,
    target_only=False,
    make_release=False,
    make_dist=False,
):
    command = ["kiwix-build"]
    command.append(target)
    command.append("--hide-progress")
    command.append("--fast-clone")
    command.append("--assume-packages-installed")
    command.append("--use-target-arch-name")
    #    command.append("--verbose")
    command.extend(["--config", config])
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
    env["SKIP_BIG_MEMORY_TEST"] = "1"
    subprocess.check_call(command, cwd=str(HOME), env=env)
    print_message("Build ended")


try:
    import paramiko

    def upload(file_to_upload, host, dest_path):
        if not file_to_upload.exists():
            print_message("No {} to upload!", file_to_upload)
            return

        if ":" in host:
            host, port = host.split(":", 1)
        else:
            port = "22"
        if "@" in host:
            user, host = host.split("@", 1)
        else:
            user = None

        from contextlib import contextmanager

        @contextmanager
        def get_client():
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.client.WarningPolicy)
            print_message(f"Connect to {host}:{port}")
            client.connect(
                host,
                port=port,
                username=user,
                key_filename=_environ.get("SSH_KEY"),
                look_for_keys=False,
                compress=True,
            )
            try:
                yield client
            finally:
                client.close()

        @contextmanager
        def get_sftp():
            with get_client() as client:
                sftp = client.open_sftp()
                try:
                    yield sftp
                finally:
                    sftp.close()

        dest_path = PurePosixPath(dest_path)
        remote_file = dest_path.joinpath(file_to_upload.name)

        with get_sftp() as sftp:
            for part in list(reversed(dest_path.parents)) + [dest_path]:
                part = str(part)
                try:
                    sftp.stat(part)
                except FileNotFoundError:
                    sftp.mkdir(part)

            print_message(f"Sending archive {file_to_upload} to {remote_file}")
            sftp.put(str(file_to_upload), str(remote_file), confirm=True)

except ModuleNotFoundError:
    # On old system (bionic) paramiko is really complex to install
    # Keep the old implementaion on sush system.

    def upload(file_to_upload, host, dest_path):
        if not file_to_upload.exists():
            print_message("No {} to upload!", file_to_upload)
            return

        if ":" in host:
            host, port = host.split(":", 1)
        else:
            port = "22"

        # sending SFTP mkdir command to the sftp interactive mode and not batch (-b) mode
        # as the latter would exit on any mkdir error while it is most likely
        # the first parts of the destination is already present and thus can't be created
        sftp_commands = "\n".join(
            [
                f"mkdir {part}"
                for part in list(reversed(Path(dest_path).parents)) + [dest_path]
            ]
        )
        command = [
            "sftp",
            "-i",
            _environ.get("SSH_KEY"),
            "-P",
            port,
            "-o",
            "StrictHostKeyChecking=no",
            host,
        ]
        print_message("Creating dest path {}", dest_path)
        subprocess.run(command, input=sftp_commands.encode("utf-8"), check=True)

        command = [
            "scp",
            "-c",
            "aes128-ctr",
            "-rp",
            "-P",
            port,
            "-i",
            _environ.get("SSH_KEY"),
            "-o",
            "StrictHostKeyChecking=no",
            str(file_to_upload),
            "{}:{}".format(host, dest_path),
        ]
        print_message("Sending archive with command {}", command)
        subprocess.check_call(command)


def upload_archive(archive, project, make_release, dev_branch=None):
    if not archive.exists():
        print_message("No archive {} to upload!", archive)
        return

    if project.startswith("kiwix-") or project in ["libkiwix"]:
        host = "ci@master.download.kiwix.org:30022"
        dest_path = "/data/download/"
    else:
        host = "ci@download.openzim.org:30022"
        dest_path = "/data/openzim/"

    if make_release:
        dest_path = dest_path + "release/" + project
    else:
        dest_path = dest_path + "nightly/" + DATE

    if dev_branch:
        dest_path = "/data/tmp/ci/dev_preview/" + dev_branch
    else:
        # Make the archive read only. This way, scp will preserve rights.
        # If somehow we try to upload twice the same archive, scp will fails.
        archive.chmod(0o444)

    upload(archive, host, dest_path)


# This remove "share/doc" and "share/man" from the thing to copy in the deps archive
def filter_install_dir(path):
    for dir in path.glob("*"):
        if dir.name not in ["share"]:
            yield dir
        else:
            for sub_dir in dir.glob("*"):
                if sub_dir.name not in ["doc", "man"]:
                    yield sub_dir


# Full: True if we are creating a full archive to be used as cache by kiwix-build (base_deps_{os}_{config}_{base_deps_version}.tar.xz)
# Full: False if we are creating a archive to be used as pre-cached dependencies for project's CI (deps_{config}_{target}.tar.xz)
def make_deps_archive(target=None, name=None, full=False):
    archive_name = name or "deps_{}_{}.tar.xz".format(
        get_dependency_archive_name(), target
    )
    print_message("Create archive {}.", archive_name)
    files_to_archive = list(filter_install_dir(INSTALL_DIR))
    files_to_archive += HOME.glob("BUILD_*/LOGS")
    if COMPILE_CONFIG == "apple_all_static":
        for subconfig in AppleXCFramework.subConfigNames:
            base_dir = get_build_dir(subconfig)
            files_to_archive += filter_install_dir(base_dir / "INSTALL")
            if (base_dir / "meson_cross_file.txt").exists():
                files_to_archive.append(base_dir / "meson_cross_file.txt")

    if COMPILE_CONFIG.endswith("_mixed"):
        static_config = COMPILE_CONFIG.replace("_mixed", "_static")
        files_to_archive += filter_install_dir(get_build_dir(static_config) / "INSTALL")
    if COMPILE_CONFIG.startswith("android_"):
        files_to_archive += filter_install_dir(HOME / "BUILD_neutral" / "INSTALL")
        base_dir = get_build_dir(COMPILE_CONFIG)
        if (base_dir / "meson_cross_file.txt").exists():
            files_to_archive.append(base_dir / "meson_cross_file.txt")
    # Copy any toolchain
    files_to_archive += [TOOLCHAIN_DIR]
    files_to_archive += HOME.glob("BUILD_neutral/TOOLCHAINS/*")
    if (BASE_DIR / "meson_cross_file.txt").exists():
        files_to_archive.append(BASE_DIR / "meson_cross_file.txt")

    manifest_file = BASE_DIR / "manifest.txt"
    write_manifest(manifest_file, archive_name, target, COMPILE_CONFIG)
    files_to_archive.append(manifest_file)

    relative_path = HOME
    if full:
        files_to_archive += ARCHIVE_DIR.glob(".*_ok")
        files_to_archive += BASE_DIR.glob("*/.*_ok")
        # Add also static build for mixed target
        if COMPILE_CONFIG.endswith("_mixed"):
            static_config = COMPILE_CONFIG.replace("_mixed", "_static")
            files_to_archive += get_build_dir(static_config).glob("*/.*_ok")
        # Native dyn and static is needed for potential cross compilation that use native tools (icu)
        files_to_archive += get_build_dir("native_dyn").glob("*/.*_ok")
        files_to_archive += get_build_dir("native_static").glob("*/.*_ok")
        files_to_archive += HOME.glob("BUILD_*android*/**/.*_ok")
        files_to_archive += HOME.glob("BUILD_*apple-macos*/**/.*_ok")
        files_to_archive += HOME.glob("BUILD_*apple-ios*/**/.*_ok")
        files_to_archive += SOURCE_DIR.glob("*/.*_ok")
        files_to_archive += SOURCE_DIR.glob("zim-testing-suite-*/*")

    archive_file = TMP_DIR / archive_name
    with tarfile.open(str(archive_file), "w:xz") as tar:
        for name in set(files_to_archive):
            print(".{}".format(name), flush=True)
            tar.add(str(name), arcname=str(name.relative_to(relative_path)))

    return archive_file


def get_postfix(project):
    postfix = main_project_versions[project]
    extra = release_versions.get(project)
    if extra:
        postfix = "{}-{}".format(postfix, extra)
    return postfix


def make_archive(project, make_release):
    platform_name = get_platform_name()
    if not platform_name:
        return None

    try:
        base_dir, export_files = EXPORT_FILES[project]
    except KeyError:
        # No binary files to export
        return None

    if make_release:
        postfix = get_postfix(project)
    else:
        postfix = DATE

    archive_name = "{}_{}-{}".format(project, platform_name, postfix)

    files_to_archive = []
    for export_file in export_files:
        files_to_archive.extend(base_dir.glob(export_file))
    if platform_name == "win-i686":
        open_archive = lambda a: zipfile.ZipFile(
            str(a), "w", compression=zipfile.ZIP_DEFLATED
        )
        archive_add = lambda a, f: a.write(str(f), arcname=str(f.relative_to(base_dir)))
        archive_ext = ".zip"
    else:
        open_archive = lambda a: tarfile.open(str(a), "w:gz")
        archive_add = lambda a, f: a.add(
            str(f), arcname="{}/{}".format(archive_name, str(f.relative_to(base_dir)))
        )
        archive_ext = ".tar.gz"

    archive = TMP_DIR / "{}{}".format(archive_name, archive_ext)
    print_message("create archive {} with {}", archive, files_to_archive)
    with open_archive(archive) as arch:
        for f in files_to_archive:
            archive_add(arch, f)
    return archive


def create_desktop_image(make_release):
    print_message("creating desktop image")
    if make_release:
        postfix = get_postfix("kiwix-desktop")
        src_dir = SOURCE_DIR / "kiwix-desktop_release"
    else:
        postfix = DATE
        src_dir = SOURCE_DIR / "kiwix-desktop"

    if COMPILE_CONFIG == "flatpak":
        build_path = BASE_DIR / "org.kiwix.desktop.flatpak"
        app_name = "org.kiwix.desktop.{}.flatpak".format(postfix)
        print_message("archive is {}", build_path)
    else:
        build_path = HOME / "Kiwix-{}-x86_64.AppImage".format(postfix)
        app_name = "kiwix-desktop_x86_64_{}.appimage".format(postfix)
        command = [
            "kiwix-build/scripts/create_kiwix-desktop_appImage.sh",
            str(INSTALL_DIR),
            str(src_dir),
            str(HOME / "AppDir"),
        ]
        env = dict(os.environ)
        env["VERSION"] = postfix
        print_message("Build AppImage of kiwix-desktop")
        subprocess.check_call(command, cwd=str(HOME), env=env)

    print_message("Copy Build to {}".format(TMP_DIR / app_name))
    shutil.copy(str(build_path), str(TMP_DIR / app_name))
    return TMP_DIR / app_name


def update_flathub_git():
    git_repo_dir = TMP_DIR / "org.kiwix.desktop"
    env = dict(os.environ)
    env["GIT_AUTHOR_NAME"] = env["GIT_COMMITTER_NAME"] = "KiwixBot"
    env["GIT_AUTHOR_EMAIL"] = env["GIT_COMMITTER_EMAIL"] = "release@kiwix.org"

    def call(command, cwd=None):
        cwd = cwd or git_repo_dir
        print_message("call {}", command)
        subprocess.check_call(command, env=env, cwd=str(cwd))

    command = ["git", "clone", FLATPAK_HTTP_GIT_REMOTE]
    call(command, cwd=TMP_DIR)

    branch_name = "v_{}".format(get_postfix("kiwix-desktop"))
    command = ["git", "checkout", "-b", branch_name]
    call(command)
    shutil.copy(str(BASE_DIR / "org.kiwix.desktop.json"), str(git_repo_dir))
    patch_dir = KBUILD_SOURCE_DIR / "kiwixbuild" / "patches"
    for dep in ["pugixml"]:
        for f in patch_dir.glob("{}_*.patch".format(dep)):
            shutil.copy(str(f), str(git_repo_dir / "patches"))
    command = ["git", "add", "-A", "."]
    call(command)
    command = [
        "git",
        "commit",
        "-m",
        "Update to version {}".format(get_postfix("kiwix-desktop")),
    ]
    try:
        call(command)
    except subprocess.CalledProcessError:
        # This may fail if there is nothing to commit (a rebuild of the CI for exemple)
        return
    command = ["git", "config", "remote.origin.pushurl", FLATPAK_GIT_REMOTE]
    call(command)
    command = ["git", "push", "origin", branch_name]
    env["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=no -i " + _environ.get(
        "SSH_KEY"
    )
    call(command)


def fix_macos_rpath(project):
    base_dir, export_files = EXPORT_FILES[project]
    for file in filter(lambda f: f.endswith(".dylib"), export_files):
        lib = base_dir / file
        if lib.is_symlink():
            continue
        command = ["install_name_tool", "-id", lib.name, str(lib)]
        print_message("call {}", " ".join(command))
        subprocess.check_call(command, env=os.environ)


def trigger_workflow(repo, workflow="docker.yml", ref="main", inputs=None):
    """triggers a `workflow_dispatch` event to the specified workflow on its repo

    repo: {user}/{repo} format
    workflow: workflow ID or workflow file name
    ref: branch or tag name
    inputs: dict of inputs to pass to the workflow"""
    print_message(
        "triggering workflow `{workflow}` on {repo}@{ref} " "with inputs={inputs}",
        workflow=workflow,
        repo=repo,
        ref=ref,
        inputs=inputs,
    )

    url = "{base_url}/repos/{repo}/actions/workflows/{workflow}/dispatches".format(
        base_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
        repo=repo,
        workflow=workflow,
    )

    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": "token {token}".format(token=os.getenv("GITHUB_PAT", "")),
            "Accept": "application/vnd.github.v3+json",
        },
        json={"ref": ref, "inputs": inputs},
        timeout=5,
    )
    if resp.status_code != 204:
        raise ValueError(
            "Unexpected HTTP {code}: {reason}".format(
                code=resp.status_code, reason=resp.reason
            )
        )


def trigger_docker_publish(target):
    if target not in ("zim-tools", "kiwix-tools"):
        return

    version = get_postfix(target)
    repo = {"zim-tools": "openzim/zim-tools", "kiwix-tools": "kiwix/kiwix-tools"}.get(
        target
    )

    try:
        trigger_workflow(
            repo, workflow="docker.yml", ref="main", inputs={"version": version}
        )
        print_message("triggered docker workflow on {repo}", repo=repo)
    except Exception as exc:
        print_message("Error triggering workflow: {exc}", exc=exc)
        raise exc


def notarize_macos_build(project):
    """sign and notarize files for macOS

    Expects the following environment:
    - `SIGNING_IDENTITY` environ with Certificate name/identity
    - `KEYCHAIN` environ with path to the keychain storing credentials
    - `KEYCHAIN_PROFILE` environ with name of the profile in that keychain
    - `KEYCHAIN_PASSWORD` environ with password to unlock the keychain
    """
    if project != "libzim":
        return

    # currently only supports libzim use case: sign every dylib
    base_dir, export_files = EXPORT_FILES[project]
    filepaths = [
        base_dir.joinpath(file)
        for file in filter(lambda f: f.endswith(".dylib"), export_files)
        if not base_dir.joinpath(file).is_symlink()
    ]

    if not filepaths:
        return

    for filepath in filepaths:
        subprocess.check_call(
            [
                "/usr/bin/codesign",
                "--force",
                "--sign",
                os.getenv("SIGNING_IDENTITY", "no-signing-ident"),
                "--keychain",
                os.getenv("KEYCHAIN", "no-keychain-path"),
                str(filepath),
                "--deep",
                "--timestamp",
            ],
            env=os.environ,
        )

    # create a zip of the dylibs and upload for notarization
    zip_name = "{}.zip".format(project)
    subprocess.check_call(
        ["/usr/bin/ditto", "-c", "-k", "--keepParent"]
        + [str(f) for f in filepaths]
        + [zip_name],
        env=os.environ,
    )

    # make sure keychain is unlocked
    subprocess.check_call(
        [
            "/usr/bin/security",
            "unlock-keychain",
            "-p",
            os.getenv("KEYCHAIN_PASSWORD", "no-keychain-password"),
            os.getenv("KEYCHAIN", "no-keychain-path"),
        ],
        env=os.environ,
    )

    subprocess.check_call(
        [
            "/usr/bin/xcrun",
            "notarytool",
            "submit",
            "--keychain",
            os.getenv("KEYCHAIN", "no-keychain-path"),
            "--keychain-profile",
            os.getenv("KEYCHAIN_PROFILE", "no-keychain-profile"),
            "--wait",
            str(zip_name),
        ],
        env=os.environ,
    )

    # check notarization of a file (should be in-progress atm and this != 0)
    subprocess.call(
        ["/usr/sbin/spctl", "--assess", "-vv", "--type", "install", filepaths[-1]],
        env=os.environ,
    )
