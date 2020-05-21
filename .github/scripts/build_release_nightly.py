#!/usr/bin/env python3

import os
import json
import shutil

from common import (
    run_kiwix_build,
    main_project_versions,
    release_versions,
    get_postfix,
    make_archive,
    create_desktop_image,
    update_flathub_git,
    upload_archive,
    BASE_DIR,
    TMP_DIR,
    HOME,
    OS_NAME,
    PLATFORM_TARGET,
    DESKTOP,
)

from upload_to_bintray import upload_from_json


if os.environ.get('GITHUB_EVENT_NAME') == 'schedule':
    RELEASE = False
else:
    RELEASE = True

if PLATFORM_TARGET == "android":
    TARGETS = ("kiwix-lib-app",)
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
            TARGETS = ("zimwriterfs", "zim-tools", "kiwix-tools")
elif PLATFORM_TARGET in ("win32_static", "armhf_static", "i586_static"):
    TARGETS = ("kiwix-tools",)
elif PLATFORM_TARGET == "flatpak":
    TARGETS = ("kiwix-desktop",)
else:
    TARGETS = ("libzim", "zim-tools", "kiwix-lib", "kiwix-tools")

# Filter what to build if we are doing a release.
if RELEASE:
    TARGETS = tuple(filter(lambda t: release_versions.get(t) is not None, TARGETS))

for target in TARGETS:
    run_kiwix_build(target, platform=PLATFORM_TARGET, make_release=RELEASE)
    if target == "kiwix-desktop":
        archive = create_desktop_image(make_release=RELEASE)
    else:
        archive = make_archive(target, make_release=RELEASE)
    if archive:
        upload_archive(archive, target, make_release=RELEASE)

# We have few more things to do for release:
if RELEASE:
    # Publish source archives
    if PLATFORM_TARGET == "native_dyn" and OS_NAME != "osx":
        for target in TARGETS:
            if release_versions.get(target) != 0:
                continue
            run_kiwix_build(
                target, platform=PLATFORM_TARGET, make_release=RELEASE, make_dist=True
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
            upload_archive(archive, target, make_release=RELEASE)

    # Publish flathub
    if PLATFORM_TARGET == "flatpak" and "kiwix-desktop" in TARGETS:
        update_flathub_git()

    if PLATFORM_TARGET == "android" and "kiwix-lib-app" in TARGETS:
        postfix = get_postfix("kiwix-lib")
        basename = "kiwixlib-{}".format(postfix)

        output_release_dir = (
            HOME / "BUILD_android" / "kiwix-lib-app" / "kiwixLibAndroid" / "build"
        )
        shutil.copy(
            str(output_release_dir / "outputs" / "aar" / "kiwixLibAndroid-release.aar"),
            str(TMP_DIR / (basename + ".aar")),
        )
        shutil.copy(
            str(output_release_dir / "pom.xml"), str(TMP_DIR / (basename + ".pom"))
        )

        json_filename = "{}_bintray_info.json".format(basename)
        data = {
            "version": postfix,
            "files": [basename + ext for ext in (".aar", ".pom")],
        }
        with open(str(TMP_DIR / json_filename), "w") as f:
            json.dump(data, f)

        upload_from_json(TMP_DIR / json_filename)
