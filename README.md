Build status: [![Build Status](https://travis-ci.org/kiwix/kiwix-build.svg?branch=master)](https://travis-ci.org/kiwix/kiwix-build)

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

```
$ sudo apt-get install python3-pip virtualenv
```

Create a virtual environment to install python module in it instead
of modifying the system.
```
$ virtualenv -p python3 ./ # Create virtualenv
$ source bin/activate      # Activate the virtualenv
```

Then, download and install kiwix-build and its dependencies:
```
$ git clone git://github.com/kiwix/kiwix-build.git
$ cd kiwix-build
$ pip install .
$ hash -r                  # Refresh bash paths
```

If your distribution doesn't provide ninja version > 1.6 you can get it
this way :

```
$ wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
$ unzip ninja-linux.zip ninja -d $HOME/bin
```

# Compilation

The compilation is handled by the `kiwix-build` command. It will compile
everything. If you are using a supported platform (Redhat or Debian
based) it will install missing packages using `sudo`. You can get
`kiwix-build` usage like this:

```
$ kiwix-build --help
```

## Target

You may want to compile a specific target so you will have to specify it on the
command line :

```
$ kiwix-build kiwix-lib # will build kiwix-build and its dependencies
$ kiwix-build zim-tools # will build zim-tools and its dependencies
```

By default, `kiwix-build` will build `kiwix-tools` .

## Target platform

By default, `kiwix-build` will build everything for the current (native)
platform using dynamic linkage (`native_dyn`).

But you can select another target platform using the option
`--target-platform`. For now, there is ten different supported
platforms :

- native_dyn
- native_static
- win32_dyn
- win32_static
- android_arm
- android_arm64
- android_mips
- android_mips64
- android_x86
- android_x86_64

So, if you want to compile `kiwix-tools` for win32 using static linkage:

```
$ kiwix-build --target-platform win32_dyn
```

Or, android apk for android_arm :
```
$ kiwix-build --target-platform android_arm kiwix-android
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
