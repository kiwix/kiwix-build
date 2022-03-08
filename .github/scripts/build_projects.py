#!/usr/bin/env python3


from common import (
    run_kiwix_build,
    make_archive,
    create_desktop_image,
    fix_macos_rpath,
    OS_NAME,
    PLATFORM_TARGET,
    DESKTOP,
    notarize_macos_build,
)

if PLATFORM_TARGET.startswith("android_"):
    TARGETS = ("libkiwix",)
elif PLATFORM_TARGET.startswith("iOS"):
    TARGETS = ("libzim", "libkiwix")
elif PLATFORM_TARGET.startswith("native_"):
    if OS_NAME == "osx":
        if PLATFORM_TARGET == "native_mixed":
            TARGETS = ("libzim", )
        else:
            TARGETS = ("libzim", "zim-tools", "libkiwix")
    else:
        if DESKTOP:
            TARGETS = ("kiwix-desktop",)
        elif PLATFORM_TARGET == "native_mixed":
            TARGETS = ("libzim",)
        else:
            TARGETS = ("zim-tools", "libkiwix", "kiwix-tools")
elif PLATFORM_TARGET in ("win32_static", "armhf_static", "i586_static"):
    TARGETS = ("kiwix-tools",)
elif PLATFORM_TARGET == "flatpak":
    TARGETS = ("kiwix-desktop",)
else:
    TARGETS = ("libzim", "zim-tools", "libkiwix", "kiwix-tools")

for target in TARGETS:
    run_kiwix_build(target, platform=PLATFORM_TARGET)
    if target == "kiwix-desktop":
        create_desktop_image(make_release=False)
    else:
        if PLATFORM_TARGET == "native_mixed" and OS_NAME == "osx":
            fix_macos_rpath(target)
            notarize_macos_build(target)
        make_archive(target, make_release=False)
