#!/usr/bin/env python3


from common import (
    run_kiwix_build,
    make_archive,
    create_desktop_image,
    fix_macos_rpath,
    upload_archive,
    OS_NAME,
    PLATFORM_TARGET,
    DEV_BRANCH,
)


def select_build_target():
    from common import (
        PLATFORM_TARGET,
        DESKTOP,
        OS_NAME
    )
    if OS_NAME == "bionic" and PLATFORM_TARGET.endswith("_mixed"):
        return ("libzim", )
    elif (PLATFORM_TARGET.startswith("android_")
     or PLATFORM_TARGET.startswith("iOS")):
        return ("libzim", "libkiwix")
    elif PLATFORM_TARGET.startswith("macOS"):
        if PLATFORM_TARGET.endswith("_mixed"):
            return ("libzim", "libkiwix")
        else:
            return ("zim-tools", "kiwix-tools")
    elif PLATFORM_TARGET.startswith("native_"):
        if OS_NAME == "osx":
            if PLATFORM_TARGET.endswith("_mixed"):
                return ("libzim", "libkiwix")
            else:
                return ("zim-tools", "kiwix-tools")
        else:
            if DESKTOP:
                return ("kiwix-desktop",)
            elif PLATFORM_TARGET == "native_mixed":
                return ("libzim", "libkiwix")
            else:
                return ("zim-tools", "kiwix-tools")
    elif PLATFORM_TARGET in ("win32_static", "armhf_static", "armhf_dyn", "aarch64_static", "aarch64_dyn", "i586_static"):
        return ("zim-tools", "kiwix-tools")
    elif PLATFORM_TARGET == "flatpak":
        return ("kiwix-desktop",)
    elif PLATFORM_TARGET in ("wasm", "armhf_mixed", "aarch64_mixed"):
        return ("libzim", )
    else:
        return ("libzim", "zim-tools", "libkiwix", "kiwix-tools")

TARGETS = select_build_target()

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
