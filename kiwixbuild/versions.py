# This file reference all the versions of the depedencies we use in kiwix-build.

main_project_versions = {
    "libzim": "9.4.0",
    "libkiwix": "14.1.1",
    "kiwix-tools": "3.8.1",
    "zim-tools": "3.6.0",
    "kiwix-desktop": "2.4.1",
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
    "libzim": None,  # Depends of base deps (was 1)
    "libkiwix": None,  # Depends of libzim (was 0)
    "kiwix-tools": 0,  # Depends of libkiwix and libzim (was None)
    "zim-tools": None,  # Depends of libzim (was 0)
    "kiwix-desktop": None,  # Depends of libkiwix and libzim (was 0)
}


# This is the "version" of the whole base_deps_versions dict.
# Change this when you change base_deps_versions.
base_deps_meta_version = "18"

# Base dependencies defined as Dependency objects
class Dependency:
    """Represents an external dependency with its version."""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    def __repr__(self) -> str:
        return f"Dependency(name={self.name}, version={self.version})"

base_deps = [
    Dependency("zlib", "1.3.1"),
    Dependency("lzma", "5.2.6"),
    Dependency("zstd", "1.5.2"),
    Dependency("docoptcpp", "0.6.2"),
    Dependency("uuid", "1.47.3"),
    Dependency("xapian-core", "1.4.26"),
    Dependency("mustache", "4.1"),
    Dependency("pugixml", "1.15"),
    Dependency("libmicrohttpd", "0.9.76"),
    Dependency("gumbo", "0.13.1"),
    Dependency("icu4c", "73.2"),
    Dependency("libaria2", "1.37.0"),
    Dependency("libmagic", "5.44"),
    Dependency("android-ndk", "r23c"),
    Dependency("org.kde", "6.9"),
    Dependency("io.qt.qtwebengine", "6.9"),
    Dependency("zim-testing-suite", "0.8.0"),
    Dependency("emsdk", "3.1.41"),
]

# Backward compatibility:
# Keep the dict form for existing code paths
base_deps_versions = {
    dep.name: dep.version for dep in base_deps
}