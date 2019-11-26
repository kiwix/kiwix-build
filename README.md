Build status: [![Build Status](https://travis-ci.com/kiwix/kiwix-build.svg?branch=master)](https://travis-ci.com/kiwix/kiwix-build)

Kiwix is an offline reader for web content. It's especially thought to
make Wikipedia available offline. This is done by reading the content
of the project stored in a file format ZIM, a high compressed open
format with additional meta-data.

This repository contains advanced tools to (cross-)compile easily
Kiwix softwares and library and deploy them. They have been tested on
Fedora 23 and Ubuntu 16.10.

# Prerequesites

You will need a recent version of `meson` (0.34) and `ninja` (1.6) If
your distribution provides a recent enough versions for them, just
install them with your package manager. Continue to read the
instructions otherwise.

Before anything else you need to install Python3 related tools. On Debian
based systems:
```bash
sudo apt-get install python3-pip virtualenv
```

Create a virtual environment to install python module in it instead
of modifying the system.
```bash
virtualenv -p python3 ./ # Create virtualenv
source bin/activate      # Activate the virtualenv
```

Then, download and install kiwix-build and its dependencies:
```bash
git clone https://github.com/kiwix/kiwix-build.git
cd kiwix-build
pip install .
hash -r                  # Refresh bash paths
```

If your distribution doesn't provide ninja version > 1.6 you can get it
this way :
```bash
wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
unzip ninja-linux.zip ninja -d $HOME/bin
```

# Compilation

The compilation is handled by the `kiwix-build` command. It will compile
everything. If you are using a supported platform (Redhat or Debian
based) it will install missing packages using `sudo`. You can get
`kiwix-build` usage like this:
```bash
kiwix-build --help
```

## Target

You may want to compile a specific target so you will have to specify it on the
command line :
```bash
kiwix-build kiwix-lib # will build kiwix-build and its dependencies
kiwix-build zim-tools # will build zim-tools and its dependencies
```

By default, `kiwix-build` will build `kiwix-tools` .

## Target platform

If no target platform is specified, a default one will be infered from
the specified target :
- `kiwix-android` will be build using the platform `android`
- Other targets will be build using the platform `native_dyn`

But you can select another target platform using the option
`--target-platform`. For now, there is ten different supported
platforms :

- native_dyn
- native_static
- win32_dyn
- win32_static
- android
- android_arm
- android_arm64
- android_x86
- android_x86_64

So, if you want to compile `kiwix-tools` for win32 using static linkage:
```bash
kiwix-build --target-platform win32_dyn
```

## Android

Android apk (kiwix-android) is a bit a special case.
`kiwix-android` itself is architecture independent (it is written in
java) but it use `kiwix-lib` who is architecture dependent.

When building `kiwix-lib`, you should directly use the
target-platform `android_<arch>`:
```bash
kiwix-build kiwix-lib --target-platform android_arm
```

But, `kiwix-android` apk can also be multi arch (ie, it includes
`kiwix-lib` for several architectures). To do so, you must ask to build
`kiwix-android` using the `android` platform:
```bash
kiwix-build --target-platform android kiwix-android
kiwix-build kiwix-android # because `android` platform is the default for `kiwix-android`
```

By default, when using platform `android`, `kiwix-lib` will be build for
all architectures. This can be changed by using the option `--android-arch` :
```bash
kiwix-build kiwix-android # apk for all architectures
kiwix-build kiwix-android --android-arch arm # apk for arm architecture
kiwix-build kiwix-anrdoid --android-arch arm --android-arch arm64 # apk for arm and arm64 architectures
```

## IOS

When building for ios, we may want to compile a "fat library", a library
for several architectures.

To do so, you should directly use the target-platfrom `ios_multi`.
As for `android`, `kiwix-build` will build the library several times
(once for each platform) and then create the fat library.
```bash
kiwix-build --target-platform iOS_multi kiwix-lib
```

You can specify the supported architectures with the option `--ios-arch`:
```bash
kiwix-build --target-platform iOS_multi kiwix-lib # all architetures
kiwix-build --target-platform iOS_multi --ios-arch arm --ios-arch arm64 # arm and arm64 arch only
```


# Outputs

Kiwix-build.py will create several directories:
- `ARCHIVES`: All the downloaded archives go there.
- `SOURCES`: All the sources (extracted from archives and patched) go there.
- `BUILD_<target_platform>`: All the build files go there.
- `BUILD_<target_platform>/INSTALL`: The installed files go there.
- `BUILD_<target_platform>/LOGS`: The logs files of the build.

If you want to install all those directories elsewhere, you can pass the
`--working-dir` option to `kiwix-build`:
