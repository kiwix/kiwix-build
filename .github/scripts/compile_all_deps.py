#!/usr/bin/env python3

import os

from common import (
    run_kiwix_build,
    make_deps_archive,
    upload,
    COMPILE_CONFIG,
    DEV_BRANCH,
)
from build_definition import select_build_targets, DEPS

for target in select_build_targets(DEPS):
    run_kiwix_build(target, config=COMPILE_CONFIG, build_deps_only=True)
    archive_file = make_deps_archive(target=target)
    if DEV_BRANCH:
        destination = "/data/tmp/ci/dev_preview/" + DEV_BRANCH
    else:
        destination = "/data/tmp/ci"
    upload(archive_file, "ci@tmp.kiwix.org:30022", destination)
    os.remove(str(archive_file))
