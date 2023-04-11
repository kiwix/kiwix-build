#!/usr/bin/env python3


from common import (
    run_kiwix_build,
    make_archive,
    create_desktop_image,
    fix_macos_rpath,
    upload_archive,
    OS_NAME,
    PLATFORM_TARGET,
    DESKTOP,
    DEV_BRANCH,
)

if (PLATFORM_TARGET.startswith("android_")
 or PLATFORM_TARGET.startswith("iOS")
 or PLATFORM_TARGET.startswith("macOS")):
    TARGETS = ("libzim", "libkiwix")
elif PLATFORM_TARGET.startswith("native_"):
    if OS_NAME == "osx":
        if PLATFORM_TARGET.endswith("_mixed"):
            TARGETS = ("libzim", "libkiwix")
        else:
            TARGETS = ("zim-tools", )
    else:
        if DESKTOP:
            TARGETS = ("kiwix-desktop",)
        elif PLATFORM_TARGET == "native_mixed":
            TARGETS = ("libzim", "libkiwix")
        else:
            TARGETS = ("zim-tools", "kiwix-tools")
elif PLATFORM_TARGET in ("win32_static", "armhf_static", "armhf_dyn", "aarch64_static", "aarch64_dyn", "i586_static"):
    TARGETS = ("zim-tools", "kiwix-tools")
elif PLATFORM_TARGET == "flatpak":
    TARGETS = ("kiwix-desktop",)
elif PLATFORM_TARGET in ("wasm", "armhf_mixed", "aarch64_mixed"):
    TARGETS = ("libzim", )
else:
    TARGETS = ("libzim", "zim-tools", "libkiwix", "kiwix-tools")

for target in TARGETS:
    run_kiwix_build(target, platform=PLATFORM_TARGET)
    if target == "kiwix-desktop":
        archive = create_desktop_image(make_release=False)
    else:
        if PLATFORM_TARGET == "native_mixed" and OS_NAME == "osx":
            fix_macos_rpath(target)
        archive = make_archive(target, make_release=False)
    if archive and DEV_BRANCH:
        upload_archive(archive, target, make_release=False, dev_branch=DEV_BRANCH)
