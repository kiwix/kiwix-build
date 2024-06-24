#!/usr/bin/env python3

from build_definition import select_build_targets, BUILD
from common import (
    run_kiwix_build,
    make_archive,
    create_desktop_image,
    fix_macos_rpath,
    upload_archive,
    OS_NAME,
    COMPILE_CONFIG,
    DEV_BRANCH,
)

for target in select_build_targets(BUILD):
    run_kiwix_build(target, config=COMPILE_CONFIG, make_release=True)
    if target == "kiwix-desktop":
        archive = create_desktop_image(make_release=False)
    else:
        if COMPILE_CONFIG == "native_mixed" and OS_NAME == "macos":
            fix_macos_rpath(target)
        archive = make_archive(target, make_release=False)
    if archive and DEV_BRANCH:
        upload_archive(archive, target, make_release=False, dev_branch=DEV_BRANCH)
