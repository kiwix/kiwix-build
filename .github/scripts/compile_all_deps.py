#!/usr/bin/env python3

import os

from common import (
    run_kiwix_build,
    make_deps_archive,
    upload,
    print_message,
    should_upload,
    COMPILE_CONFIG,
    DEV_BRANCH,
)
from build_definition import select_build_targets, DEPS

skip_upload = not should_upload()

for target in select_build_targets(DEPS):
    run_kiwix_build(target, config=COMPILE_CONFIG, build_deps_only=True)
    archive_file = make_deps_archive(target=target)
    if DEV_BRANCH:
        destination = "/data/tmp/ci/dev_preview/" + DEV_BRANCH
    else:
        destination = "/data/tmp/ci"

    upload(archive_file, "ci@tmp.kiwix.org:30022", destination, skip_upload=skip_upload)
    os.remove(str(archive_file))
