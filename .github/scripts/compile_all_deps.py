#!/usr/bin/env python3

import os

from common import (
    run_kiwix_build,
    make_deps_archive,
    upload,
    OS_NAME,
    PLATFORM_TARGET,
    DESKTOP,
    KIWIX_DESKTOP_ONLY,
)
from build_definition import select_build_targets, DEPS

for target in select_build_targets(DEPS):
    run_kiwix_build(target, platform=PLATFORM_TARGET, build_deps_only=True)
    archive_file = make_deps_archive(target=target)
    upload(archive_file, "ci@tmp.kiwix.org:30022", "/data/tmp/ci")
    os.remove(str(archive_file))
