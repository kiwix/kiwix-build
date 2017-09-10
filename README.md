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
sudo apt-get install python3-pip virtualenv
```

Then install Meson:
```
virtualenv -p python3 ./         # Create virtualenv
source bin/activate              # Activate the virtualenv
pip3 install -r requirements.txt # Install Python dependencies
hash -r                          # Refresh bash paths
```

Finally we need the Ninja tool (available in the $PATH). Here is a
solution to download, build and install it locally:

```
git clone git://github.com/ninja-build/ninja.git
cd ninja
git checkout release
./configure.py --bootstrap
mkdir ../bin
cp ninja ../bin
cd ..
```

# Compilation

The compilation is handled by `kiwix-build.py`. It will compile
everything. If you are using a supported platform (Redhat or Debian
based) it will install missing packages using `sudo`. You can get
`kiwix-build.py` usage like this:

```
./kiwix-build.py -h
```

## Target

By default, `kiwix-build.py` will build `kiwix-tools`. If you want to
compile another target only (let's said kiwixlib), you can specify it:

```
./kiwix-build Kiwixlib
```

## Target platform

By default, `kiwix-build.py` will build everything for the current (native)
platform using dynamic linkage (hence the `native_dyn` of the
BUILD_native_dyn directory).

But you can select another target platform using the option
`target-platform`. For now, there is ten different supported
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

So, if you want to compile for win32 using static linkage:

```
./kiwix-build.py --target-platform win32_dyn
```

# Outputs

Kiwix-build.py will create several directories:
- `ARCHIVES`: All the downloaded archives go there.
- `SOURCES`: All the sources (extracted from archives and patched) go there.
- `BUILD_native_dyn`: All the build files go there.
- `BUILD_native_dyn/INSTALL`: The installed files go there.
- `BUILD_native_dyn/LOGS`: The logs files of the build.

If you want to install all those directories elsewhere, you can pass the
`--working-dir` option to `kiwix-build.py`:
