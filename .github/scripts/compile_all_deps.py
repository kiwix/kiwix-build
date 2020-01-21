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

if PLATFORM_TARGET.startswith("android_"):
    TARGETS = ("libzim", "kiwix-lib")
elif PLATFORM_TARGET.startswith("iOS"):
    TARGETS = ("libzim", "kiwix-lib")
elif PLATFORM_TARGET.startswith("native_"):
    if OS_NAME == "osx":
        TARGETS = ("libzim", "zimwriterfs", "zim-tools", "kiwix-lib")
    else:
        if DESKTOP:
            TARGETS = ("kiwix-desktop",)
        elif PLATFORM_TARGET == "native_mixed":
            TARGETS = ("libzim",)
        else:
            TARGETS = ("libzim", "zimwriterfs", "zim-tools", "kiwix-lib", "kiwix-tools")
else:
    TARGETS = ("libzim", "zim-tools", "kiwix-lib", "kiwix-tools")

for target in TARGETS:
    run_kiwix_build(target, platform=PLATFORM_TARGET, build_deps_only=True)
    archive_file = make_deps_archive(target=target)
    upload(archive_file, "ci@tmp.kiwix.org", "/data/tmp/ci")
    os.remove(str(archive_file))
