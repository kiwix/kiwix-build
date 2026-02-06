# This file reference all the versions of the depedencies we use in kiwix-build.

main_project_versions = {
    "libzim": "9.5.0",
    "libkiwix": "14.1.1",
    "kiwix-tools": "3.8.1",
    "zim-tools": "3.6.0",
    "kiwix-desktop": "2.5.1",
}

# This dictionnary specify what we need to build at each release process.
# - Values are integer or None
# - If a project is not in the dict (or None), the project is not released.
# - If release_versions[project] == 0, this is the first time the project is
#   build for this release, so publish src and build archives.
# - If release_versions[project] > 0, release only the build archive with a
#   build postfix.
# To change this dictionnary, use the following algorithm:
# - If project version change, set release_versions[project] = 0
# - Else
#    - If project depedencies have not change, set it to None and update the
#     `(was ...)`.
#    - Else, increment the value. If no value was present, see `(was ...)`.

release_versions = {
    "libzim": None,  # Depends of base deps (was 0)
    "libkiwix": 1,  # Depends of libzim (was none)
    "kiwix-tools": None,  # Depends of libkiwix and libzim (was 0)
    "zim-tools": None,  # Depends of libzim (was 0)
    "kiwix-desktop": None,  # Depends of libkiwix and libzim (was 0)
}


# This is the "version" of the whole base_deps_versions dict.
# Change this when you change base_deps_versions.
base_deps_meta_version = "20"

base_deps_versions = {
    "zlib": "1.3.1",
    "lzma": "5.2.6",
    "zstd": "1.5.2",
    "docoptcpp": "0.6.2",
    "uuid": "1.47.3",
    "xapian-core": "1.4.26",
    "mustache": "4.1",
    "pugixml": "1.15",
    "libmicrohttpd": "0.9.76",
    "gumbo": "0.13.1",
    "icu4c": "73.2",
    "libaria2": "1.37.0",
    "libmagic": "5.44",
    "android-ndk": "r23c",
    "org.kde": "6.10",
    "io.qt.qtwebengine": "6.10",
    "zim-testing-suite": "0.9.0",
    "emsdk": "3.1.41",
}
