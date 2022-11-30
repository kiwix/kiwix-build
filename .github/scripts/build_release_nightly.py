#!/usr/bin/env python3

import os

from common import (
    run_kiwix_build,
    main_project_versions,
    release_versions,
    make_archive,
    create_desktop_image,
    update_flathub_git,
    upload_archive,
    fix_macos_rpath,
    trigger_docker_publish,
    BASE_DIR,
    TMP_DIR,
    HOME,
    OS_NAME,
    PLATFORM_TARGET,
    DESKTOP,
    MAKE_RELEASE,
    notarize_macos_build,
)

if PLATFORM_TARGET.startswith("android_") or PLATFORM_TARGET.startswith("iOS"):
    TARGETS = ("libzim", "libkiwix")
elif PLATFORM_TARGET.startswith("native_"):
    if OS_NAME == "osx":
        if PLATFORM_TARGET == "native_mixed":
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
elif PLATFORM_TARGET in ("win32_static", "armhf_static", "i586_static"):
    TARGETS = ("kiwix-tools",)
elif PLATFORM_TARGET == "flatpak":
    TARGETS = ("kiwix-desktop",)
elif PLATFORM_TARGET == "wasm":
    TARGETS = ("libzim", )
else:
    TARGETS = ("libzim", "zim-tools", "libkiwix", "kiwix-tools")

# Filter what to build if we are doing a release.
if MAKE_RELEASE:
    def release_filter(project):
        return release_versions.get(project) is not None
    TARGETS = tuple(filter(release_filter, TARGETS))

for target in TARGETS:
    run_kiwix_build(target, platform=PLATFORM_TARGET, make_release=MAKE_RELEASE)
    if target == "kiwix-desktop":
        archive = create_desktop_image(make_release=MAKE_RELEASE)
    else:
        if PLATFORM_TARGET == "native_mixed" and OS_NAME == "osx":
            fix_macos_rpath(target)
            notarize_macos_build(target)
        archive = make_archive(target, make_release=MAKE_RELEASE)
    if archive:
        upload_archive(archive, target, make_release=MAKE_RELEASE)
        if MAKE_RELEASE and target in ("zim-tools", "kiwix-tools"):
            trigger_docker_publish(target)

# We have few more things to do for release:
if MAKE_RELEASE:
    # Publish source archives
    if PLATFORM_TARGET in ("native_dyn", "native_mixed") and OS_NAME != "osx":
        for target in TARGETS:
            if release_versions.get(target) != 0:
                continue
            run_kiwix_build(
                target, platform=PLATFORM_TARGET, make_release=MAKE_RELEASE, make_dist=True
            )
            full_target_name = "{}-{}".format(target, main_project_versions[target])
            if target == "kiwix-desktop":
                archive = (
                    BASE_DIR / full_target_name / "{}.tar.gz".format(full_target_name)
                )
            else:
                archive = (
                    BASE_DIR
                    / full_target_name
                    / "meson-dist"
                    / "{}.tar.xz".format(full_target_name)
                )
            upload_archive(archive, target, make_release=MAKE_RELEASE)

    # Publish flathub
    if PLATFORM_TARGET == "flatpak" and "kiwix-desktop" in TARGETS:
        update_flathub_git()
