Build status : [![Build Status](https://travis-ci.org/kiwix/kiwix-build.svg?branch=master)](https://travis-ci.org/kiwix/kiwix-build)


Kiwix is an offline reader for Web content. It's especially thought to
make Wikipedia available offline.  This is done by reading the content
of the project stored in a file format ZIM, a high compressed open
format with additional meta-data.

This repository contains a set of tools to help development or usage
of kiwix.

# COMPILATION INSTRUCTIONS

Most of the compilation steps are handled by the kiwix-build.py
script.

This script has been tested on Fedora 23 and Ubuntu 16.10

If you want to cross-compile for other platforms as windows or android, you
should read the "Other target platform" section.

This script is not officially supported on Debian 8, but has been reported to work, after adding ~/.local/bin to the PATH.

## Preparing environment

You will need a recent version of meson (0.34) and ninja (1.6)
If your distribution provide a recent enough versions for them, just install
them with your package manager.

Else you can install them manually

### Meson
You need to install python 3 and pip. On debian and ubuntu, they are provided by the package python3-pip

```
pip3 install meson --user # Install Meson
```

(You may want to install meson in a virtualenv if you prefer)

### ninja
You need git to be installed

```
git clone git://github.com/ninja-build/ninja.git
cd ninja
git checkout release
./configure.py --bootstrap
cp ninja <a_directory_in_your_path>
```

## Buildings

This is the simple one.

```
./kiwix-build.py
```

It will compile everything.
If you are using a supported platform (redhat or debian based) it will install
missing packages using sudo.
If you don't want to trust kiwix-build.py and give it the root right, just
launch yourself the printed command.

### Outputs

Kiwix-build.py will create several directories:

- ARCHIVES : All the downloaded archives go there.
- SOURCES : All the sources (extracted from archives and patched) go there.
- BUILD_native_dyn : All the build files go there.
- BUILD_native_dyn/INSTALL : The installed files go there.
- BUILD_native_dyn/LOGS: The logs files of the build.

ARCHIVES and SOURCES are independent of the build type you choose.

If you want to install all those directories elsewhere, you can pass the
`--working-dir` option:

```
./kiwix-build.py --working-dir <a_directory_somewhere>
```

### Other target

By default, kiwix-build will build kiwix-tools and all its dependencies.
If you want to compile another target only (let's said kiwixlib), you can
specify it:

```
./kiwix-build Kiwixlib
```

### Other target platform.

By default, kiwix-build will build everything for the current (native) platform
using dynamic linkage (hence the `native_dyn` of the BUILD_native_dyn directory).

But you can select another target platform using the option `target-platform`.
For now, there is ten different supported platforms :

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

As said before, the ARCHIVES and SOURCES directories are common to all target
platforms. So, if you always work in the same working directory the sources
will not be downloaded and prepared again.

On android* platforms, only kiwixlib is supported. So you must ask to
kiwix-build to compile only kiwixlib:

```
./kiwix-build.py --target-platform android_arm Kiwixlib
```

## Know bugs

- The script has not been tested on Mac OSX.
- Cross-compilation to arm (raspberry-PI) is missing.

Help is welcome on those parts.


# CONTACT

IRC: #kiwix on irc.freenode.net  
(I'm hidding myself under the starmad pseudo)

You can use IRC web interface on http://chat.kiwix.org/

More... http://www.kiwix.org/wiki/Communication

# LEGAL & DISCLAIMER

Read 'COPYING' file
