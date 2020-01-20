#!/usr/bin/env python3

import os
import tarfile
from urllib.request import urlopen
from urllib.error import URLError

from kiwixbuild.versions import base_deps_meta_version

from common import (
    print_message,
    run_kiwix_build,
    upload,
    make_deps_archive,
    HOME,
    PLATFORM_TARGET,
    OS_NAME,
    MAKE_RELEASE,
)


def download_base_archive(base_name):
    url = "http://tmp.kiwix.org/ci/{}".format(base_name)
    file_path = str(HOME / base_name)
    batch_size = 1024 * 1024 * 8
    with urlopen(url) as resource, open(file_path, "wb") as file:
        while True:
            batch = resource.read(batch_size)
            if not batch:
                break
            print(".", end="", flush=True)
            file.write(batch)
    return file_path


ARCHIVE_NAME_TEMPLATE = "base_deps2_{os}_{platform}_{version}_{release}.tar.xz"
base_dep_archive_name = ARCHIVE_NAME_TEMPLATE.format(
    os=OS_NAME,
    platform=PLATFORM_TARGET,
    version=base_deps_meta_version,
    release="release" if MAKE_RELEASE else "debug",
)

print_message("Getting archive {}", base_dep_archive_name)
try:
    local_filename = download_base_archive(base_dep_archive_name)
    with tarfile.open(local_filename) as f:
        f.extractall(str(HOME))
    os.remove(str(local_filename))
except URLError:
    print_message("Cannot get archive. Build dependencies")
    if PLATFORM_TARGET == "android":
        for arch in ("arm", "arm64", "x86", "x86_64"):
            archive_name = ARCHIVE_NAME_TEMPLATE.format(
                os=OS_NAME,
                platform="android_{}".format(arch),
                version=base_deps_meta_version,
                release="release" if MAKE_RELEASE else "debug",
            )
            print_message("Getting archive {}", archive_name)
            try:
                local_filename = download_base_archive(archive_name)
                with tarfile.open(local_filename) as f:
                    f.extractall(str(HOME))
                os.remove(str(local_filename))
            except URLError:
                pass
    else:
        run_kiwix_build("alldependencies", platform=PLATFORM_TARGET)
        archive_file = make_deps_archive(name=base_dep_archive_name, full=True)
        upload(archive_file, "ci@tmp.kiwix.org", "/data/tmp/ci")
        os.remove(str(archive_file))
