# This file reference all the versions of the depedencies we use in kiwix-build.

main_project_versions = {
    'kiwix-lib': '3.0.2',
    'kiwix-tools': '0.7.0',
    'libzim': '4.0.4',
    'zim-tools': '1.0.0',
    'zimwriterfs': '1.2',
    'kiwix-desktop': '2.0-alpha6'
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
#    - If project depedencies have not change, remove project from release_versions
#    - Else, increment the value. If no value was present, see in
#      http://download.kiwikorg/releases what to set.

release_versions = {
    'libzim': None, # Depends of base deps (was 0)
    'kiwix-lib': 0, # Depends of libzim
    'kiwix-tools': 1, # Depends of kiwix-lib and libzim
    'zim-tools': None, # Depends of libzim (was 1)
    'zimwriterfs': None, # Depends of libzim (was 1)
    'kiwix-desktop': 0 # Depends of kiwix-lib and libzim
}


# This is the "version" of the whole base_deps_versions dict.
# Change this when you change base_deps_versions.
base_deps_meta_version = '12'


base_deps_versions = {
  'zlib' : '1.2.8',
  'lzma' : '5.2.3',
  'uuid' : '1.43.4',
  'xapian-core' : '1.4.7',
  'ctpp2' : '2.8.3',
  'pugixml' : '1.2',
  'libmicrohttpd' : '0.9.46',
  'gumbo' : '0.10.1',
  'icu4c' : '58.2',
  'gradle' : '4.6',
  'libaria2' : '1.33.1',
  'libmagic' : '5.33',
  'android-sdk' : 'r25.2.3',
  'android-ndk' : 'r13b',
  'qt' : '5.10.1',
  'qtwebengine' : '5.10.1',
}
