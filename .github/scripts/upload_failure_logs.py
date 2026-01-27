#!/usr/bin/env python3

import os
import tarfile
from pathlib import Path
from common import upload, should_upload, fork_name, OS_NAME, COMPILE_CONFIG, HOME, print_message

ARCHIVE_NAME = Path(f"fail_log_{OS_NAME}_{COMPILE_CONFIG}.tar.gz")

skip_upload = not should_upload()
if skip_upload:
    print_message("Skipping failure log upload for fork: {}", fork_name())
    exit(0)

files_to_archive = []
files_to_archive += HOME.glob("BUILD_*")
files_to_archive += [HOME / "SOURCE", HOME / "LOGS", HOME / "TOOLCHAINS"]

with tarfile.open(ARCHIVE_NAME, "w:xz") as tar:
    for name in set(files_to_archive):
        tar.add(str(name))

upload(ARCHIVE_NAME, "ci@tmp.kiwix.org:30022", "/data/tmp/ci")
