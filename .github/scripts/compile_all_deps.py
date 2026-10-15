#!/usr/bin/env python3

import os

from build_definition import DEPS, select_build_targets
from common import (
    COMPILE_CONFIG,
    DEV_BRANCH,
    make_deps_archive,
    run_kiwix_build,
    upload,
)

for target in select_build_targets(DEPS):
    run_kiwix_build(target, config=COMPILE_CONFIG, build_deps_only=True)
    archive_file = make_deps_archive(target=target)
    if DEV_BRANCH:
        destination = "/data/tmp/ci/dev_preview/" + DEV_BRANCH
    else:
        destination = "/data/tmp/ci"
    upload(archive_file, "kiwix-build@tmp.kiwix.org:30522", destination)
    os.remove(str(archive_file))
