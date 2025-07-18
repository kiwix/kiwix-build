# Kiwix Build

Kiwix Build provides advanced tools to (cross-)compile easily
[Kiwix](https://kiwix.org) & [openZIM](https://openzim.org) softwares
and libraries and deploy them. They have been tested on
[Fedora](https://getfedora.org) 35+ & [Ubuntu](https://ubuntu.com)
20.04+.

Kiwix Build audience is:
* Advanced users who don't want/can handle all the dependencies
  compilations manually
* Kiwix developer team for its own CI/CD

[![CI Build Status](https://github.com/kiwix/kiwix-build/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/kiwix/kiwix-build/actions/workflows/ci.yml?query=branch%3Amain)
[![CD Build Status](https://github.com/kiwix/kiwix-build/actions/workflows/cd.yml/badge.svg?branch=main)](https://github.com/kiwix/kiwix-build/actions/workflows/cd.yml?query=branch%3Amain)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Prerequisites
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
pip3 install .
hash -r # Refresh bash paths
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
kiwix-build libkiwix # will build kiwix-build and its dependencies
kiwix-build kiwix-desktop # will build kiwix-desktop and its dependencies
kiwix-build zim-tools # will build zim-tools and its dependencies
```

By default, `kiwix-build` will build `kiwix-tools` .

To see the whole list of available targets run with non existing target, ex:

```bash
kiwix-build not-existing-target
...
invalid choice: 'not-existing-target' (choose from 'alldependencies', 'android-ndk',
...
```

#### Config

If no config is specified, the default will be `native_dyn`.

You can select another config using the option
`--config`. For now, there is ten different supported
platforms:

- native_dyn
- native_mixed
- native_static
- android
- android_arm
- android_arm64
- android_x86
- android_x86_64
- flatpak

All `native_*` config means using the native compiler without any cross-compilation option.
Other may simply use cross-compilation or may download a specific toolchain to use.

Android
-------

`kiwix-android` (https://github.com/kiwix/kiwix-android) depends of
the `libkiwix` project.

When building `libkiwix`, you should directly use the
target-platform `android_<arch>`:
```bash
kiwix-build libkiwix --config android_arm
```

You may directly use the special config `android` which will build different android architectures
```bash
kiwix-build --config android libkiwix
```

By default, it will build for all android architecture,
you can limit this with option `--android-arch`:
```bash
kiwix-build libkiwix --config android --android-arch arm # aar with arm architecture
kiwix-build libkiwix --config android --android-arch arm --android-arch arm64 # aan with arm and arm64 architectures
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
kiwix-build --config ios_multi libkiwix
```

You can specify the supported architectures with the option `--ios-arch`:
```bash
kiwix-build --config ios_multi libkiwix # all architetures
kiwix-build --config ios_multi --ios-arch arm --ios-arch arm64 # arm and arm64 arch only
```

Outputs
-------

Kiwix-build.py will create several directories:
- `ARCHIVES`: All the downloaded archives go there.
- `SOURCES`: All the sources (extracted from archives and patched) go there.
- `BUILD_<config>`: All the build files go there.
- `BUILD_<config>/INSTALL`: The installed files go there.
- `BUILD_<config>/LOGS`: The logs files of the build.

If you want to install all those directories elsewhere, you can pass the
`--working-dir` option to `kiwix-build`:

Troubleshooting
---------------

If you need to install [Meson](https://mesonbuild.com/) "manually":
```bash
virtualenv -p python3 ./ # Create virtualenv
source bin/activate      # Activate the virtualenv
pip3 install meson       # Install Meson
hash -r                  # Refresh bash paths
```

If you need to install [Ninja](https://ninja-build.org) "manually":
```bash
wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
unzip ninja-linux.zip ninja -d $HOME/bin
```

License
-------

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.
