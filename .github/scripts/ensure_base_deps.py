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
    COMPILE_CONFIG,
    OS_NAME,
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


ARCHIVE_NAME_TEMPLATE = "base_deps_{os}_{config}_{version}.tar.gz"

if COMPILE_CONFIG == "flatpak":
    base_dep_archive_name = "base_deps_flatpak.tar.gz"
else:
    base_dep_archive_name = ARCHIVE_NAME_TEMPLATE.format(
        os=OS_NAME,
        config=COMPILE_CONFIG,
        version=base_deps_meta_version,
    )

print_message("Getting archive {}", base_dep_archive_name)
try:
    local_filename = download_base_archive(base_dep_archive_name)
    with tarfile.open(local_filename) as f:
        f.extractall(str(HOME))
    os.remove(str(local_filename))
except URLError:
    if COMPILE_CONFIG == "flatpak":
        print_message("Cannot get archive. Move on")
    else:
        print_message("Cannot get archive. Build dependencies")
        run_kiwix_build("alldependencies", config=COMPILE_CONFIG)
        archive_file = make_deps_archive(name=base_dep_archive_name, full=True)
        upload(archive_file, "ci@tmp.kiwix.org:30022", "/data/tmp/ci")
        os.remove(str(archive_file))
