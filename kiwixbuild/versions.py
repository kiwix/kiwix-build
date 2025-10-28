# This file reference all the versions of the depedencies we use in kiwix-build.

main_project_versions = {
    "libzim": "9.3.0",
    "libkiwix": "14.0.0",
    "kiwix-tools": "3.7.0",
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
    "libzim": 4,  # Depends of base deps (was 3)
    "libkiwix": None,  # Depends of libzim (was 1)
    "kiwix-tools": None,  # Depends of libkiwix and libzim (was 2)
    "zim-tools": None,  # Depends of libzim (was 0)
    "kiwix-desktop": None,  # Depends of libkiwix and libzim (was 0)
}


# This is the "version" of the whole base_deps_versions dict.
# Change this when you change base_deps_versions.
base_deps_meta_version = "17"


#my code 
class Dependency:
    def __init__(self,name ,version):
        self.name=name
        self.version=version
zlib = Dependency("zlib", "1.3.1")
lzma = Dependency("lzma", "5.2.6")
zstd = Dependency("zstd", "1.5.2")
docoptcpp = Dependency("docoptcpp", "0.6.2")
uuid = Dependency("uuid", "1.43.4")
xapian_core = Dependency("xapian-core", "1.4.26")
mustache = Dependency("mustache", "4.1")
pugixml = Dependency("pugixml", "1.15")
libmicrohttpd = Dependency("libmicrohttpd", "0.9.76")
gumbo = Dependency("gumbo", "0.13.1")
icu4c = Dependency("icu4c", "73.2")
libaria2 = Dependency("libaria2", "1.37.0")
libmagic = Dependency("libmagic", "5.44")
android_ndk = Dependency("android-ndk", "r23c")
org_kde = Dependency("org.kde", "6.9")
qtwebengine = Dependency("io.qt.qtwebengine", "6.9")
zim_testing_suite = Dependency("zim-testing-suite", "0.8.0")
emsdk = Dependency("emsdk", "3.1.41")

print(emsdk.version)

        
