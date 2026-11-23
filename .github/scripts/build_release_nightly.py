#!/usr/bin/env python3


from build_definition import PUBLISH, SOURCE_PUBLISH, select_build_targets
from common import (
    BASE_DIR,
    COMPILE_CONFIG,
    MAKE_RELEASE,
    OS_NAME,
    create_desktop_image,
    fix_macos_rpath,
    main_project_versions,
    make_archive,
    notarize_macos_build,
    release_versions,
    run_kiwix_build,
    update_flathub_git,
    upload_archive,
)


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
        upload_archive(archive, target, make_release=MAKE_RELEASE)

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
        full_target_name = f"{target}-{main_project_versions[target]}"
        if target == "kiwix-desktop":
            archive = BASE_DIR / full_target_name / f"{full_target_name}.tar.gz"
        else:
            archive = (
                BASE_DIR
                / full_target_name
                / "meson-dist"
                / f"{full_target_name}.tar.xz"
            )
        upload_archive(archive, target, make_release=MAKE_RELEASE)

    # Publish flathub
    if COMPILE_CONFIG == "flatpak" and "kiwix-desktop" in TARGETS:
        update_flathub_git()
