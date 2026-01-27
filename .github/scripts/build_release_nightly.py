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
    should_upload,
    fix_macos_rpath,
    BASE_DIR,
    OS_NAME,
    COMPILE_CONFIG,
    MAKE_RELEASE,
    notarize_macos_build,
)

from build_definition import select_build_targets, BUILD, PUBLISH, SOURCE_PUBLISH

skip_upload = not should_upload()


def release_filter(project):
    return release_versions.get(project) is not None


# Filter what to build if we are doing a release.
TARGETS = select_build_targets(PUBLISH)

if MAKE_RELEASE:
    TARGETS = tuple(filter(release_filter, TARGETS))

for target in TARGETS:
    run_kiwix_build(target, config=COMPILE_CONFIG, make_release=MAKE_RELEASE)
    if target == "kiwix-desktop":
        archive = create_desktop_image(make_release=MAKE_RELEASE)
    else:
        if OS_NAME == "macos" and COMPILE_CONFIG.endswith("_mixed"):
            fix_macos_rpath(target)
            notarize_macos_build(target)
        archive = make_archive(target, make_release=MAKE_RELEASE)
    if archive:
        upload_archive(archive, target, make_release=MAKE_RELEASE, skip_upload=skip_upload)

# We have few more things to do for release:
if MAKE_RELEASE:
    # Publish source archives
    source_published_targets = select_build_targets(SOURCE_PUBLISH)
    for target in TARGETS:
        # Looping on TARGETS instead of source_published_targets ensures we are
        # publishing sources only for target we are building.
        # (source_published_targets must be a subset of TARGETS)
        if release_versions.get(target) != 0:
            continue
        if target not in source_published_targets:
            continue
        run_kiwix_build(
            target, config=COMPILE_CONFIG, make_release=MAKE_RELEASE, make_dist=True
        )
        full_target_name = "{}-{}".format(target, main_project_versions[target])
        if target == "kiwix-desktop":
            archive = BASE_DIR / full_target_name / "{}.tar.gz".format(full_target_name)
        else:
            archive = (
                BASE_DIR
                / full_target_name
                / "meson-dist"
                / "{}.tar.xz".format(full_target_name)
            )
        upload_archive(archive, target, make_release=MAKE_RELEASE, skip_upload=skip_upload)

    # Publish flathub
    if COMPILE_CONFIG == "flatpak" and "kiwix-desktop" in TARGETS:
        update_flathub_git()
