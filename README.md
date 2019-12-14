# Kiwix Build

Kiwix Build provides advanced tools to (cross-)compile easily
[Kiwix](https://kiwix.org) & [openZIM](https://openzim.org) softwares
and libraries and deploy them. They have been tested on
[Fedora](https://getfedora.org) 23+ & [Ubuntu](https://ubuntu.com)
16.10+.

[![Build Status](https://travis-ci.com/kiwix/kiwix-build.svg?branch=master)](https://travis-ci.com/kiwix/kiwix-build)

Prerequesites
-------------

You will need a recent version of [Meson](https://mesonbuild.com/) (>=
0.34) and [Ninja](https://ninja-build.org) (>= 1.6) If your
distribution provides a recent enough versions for them, just install
them with your package manager. Continue to read the instructions
otherwise.

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
hash -r # Refresh bash paths
```

If your distribution doesn't provide ninja version > 1.6 you can get it
this way:
```bash
wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
unzip ninja-linux.zip ninja -d $HOME/bin
```

Compilation
-----------

The compilation is handled by the `kiwix-build` command. It will compile
everything. If you are using a supported platform (Redhat or Debian
based) it will install missing packages using `sudo`. You can get
`kiwix-build` usage like this:
```bash
kiwix-build --help
```

#### Target

You may want to compile a specific target so you will have to specify it on the

command line:
```bash
kiwix-build kiwix-lib # will build kiwix-build and its dependencies
kiwix-build kiwix-desktop # will build kiwix-desktop and its dependencies
kiwix-build zim-tools # will build zim-tools and its dependencies
```

By default, `kiwix-build` will build `kiwix-tools` .

#### Target platform

If no target platform is specified, a default one will be infered from
the specified target:
- `kiwix-lib-app` will be build using the platform `android`
- Other targets will be build using the platform `native_dyn`

But you can select another target platform using the option
`--target-platform`. For now, there is ten different supported
platforms:

- native_dyn
- native_mixed
- native_static
- win32_dyn
- win32_static
- android
- android_arm
- android_arm64
- android_x86
- android_x86_64
- flatpak

So, if you want to compile `kiwix-tools` for win32 using static linkage:
```bash
kiwix-build --target-platform win32_dyn
```

Android
-------

`kiwix-android` (https://github.com/kiwix/kiwix-android) depends of
the `kiwix-lib` project.
It uses a special `.aar` file that represent (and embed) the kiwix-lib for
all supported android arch. This is a kind of fat archive we have for MacOs.

The `.aar` file is build using the `kiwix-lib-app` project.
`kiwix-lib-app` itself is architecture independent (it is just a packaging of
other archives) but it use `kiwix-lib` who is architecture dependent.

When building `kiwix-lib`, you should directly use the
target-platform `android_<arch>`:
```bash
kiwix-build kiwix-lib --target-platform android_arm
```

But, `kiwix-lib-app` is mainly multi arch.
To compile `kiwix-lib-app`, you must use the `android` platform:
```bash
$ kiwix-build --target-platform android kiwix-lib-app
$ kiwix-build kiwix-lib-app # because `android` platform is the default for `kiwix-lib-app`
```

By default, when using platform `android`, `kiwix-lib` will be build for
all architectures. This can be changed by using the option `--android-arch`:
```bash
$ kiwix-build kiwix-lib-app # aar with all architectures
$ kiwix-build kiwix-lib-app --android-arch arm # aar with arm architecture
$ kiwix-build kiwix-lib-app --android-arch arm --android-arch arm64 # aan with arm and arm64 architectures
```

To build `kiwix-android` itself, you should see the documentation of `kiwix-android`.

iOS
---

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

Outputs
-------

Kiwix-build.py will create several directories:
- `ARCHIVES`: All the downloaded archives go there.
- `SOURCES`: All the sources (extracted from archives and patched) go there.
- `BUILD_<target_platform>`: All the build files go there.
- `BUILD_<target_platform>/INSTALL`: The installed files go there.
- `BUILD_<target_platform>/LOGS`: The logs files of the build.

If you want to install all those directories elsewhere, you can pass the
`--working-dir` option to `kiwix-build`:
