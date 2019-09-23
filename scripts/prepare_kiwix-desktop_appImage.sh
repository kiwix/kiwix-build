#!/usr/bin/env bash

set -e

INSTALLDIR=${1:-$PWD/BUILD_native_dyn/INSTALL}
SOURCEDIR=${2:-$PWD/SOURCE/kiwix-desktop}
APPDIR=${3:-$HOME/AppDir}

SYSTEMLIBDIR=lib/x86_64-linux-gnu
# Uncoment if needed
#SYSTEMLIBDIR=lib64

#TODO We should have our icon
ICONFILE=$SOURCEDIR/resources/icons/kiwix/app_icon.svg
DESKTOPFILE=$SOURCEDIR/resources/org.kiwix.desktop.desktop

# Create structure
mkdir -p $APPDIR/usr/{bin,lib,share} $APPDIR/usr/share/applications $APPDIR/usr/share/icons/hicolor/48x48/apps
# Copy our files
cp $INSTALLDIR/bin/kiwix-desktop $APPDIR/usr/bin/
cp $INSTALLDIR/$SYSTEMLIBDIR/*.so* $APPDIR/usr/lib
# Remove it as it break with linuxdeployqt (should we compile without it) ?
rm $APPDIR/usr/lib/libmagic.so*
# Copy nss lib (to not conflict with host's ones)
cp -a /usr/$SYSTEMLIBDIR/nss $APPDIR/usr/lib
cp -a /usr/$SYSTEMLIBDIR/libstdc++.so* $APPDIR/usr/lib
cp -a /usr/$SYSTEMLIBDIR/libc.so* $APPDIR/usr/lib
cp -a /usr/$SYSTEMLIBDIR/libz.so* $APPDIR/usr/lib
cp $ICONFILE $APPDIR/kiwix-desktop.svg
cp $DESKTOPFILE $APPDIR/kiwix-desktop.desktop

# get the aria2
wget https://github.com/q3aql/aria2-static-builds/releases/download/v1.34.0/aria2-1.34.0-linux-gnu-64bit-build1.tar.bz2
mkdir -p $APPDIR/usr/bin/ && tar -C $APPDIR/usr/bin/ -xf aria2-1.34.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.34.0-linux-gnu-64bit-build1/aria2c --strip-components=1
mkdir -p $APPDIR/etc/ssl/certs/ && tar -C $APPDIR/etc/ssl/certs/ -xf aria2-1.34.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.34.0-linux-gnu-64bit-build1/ca-certificates.crt --strip-components=1

# copy kiwix-serve
cp $INSTALLDIR/bin/kiwix-serve $APPDIR/usr/bin

# Get linuxdeployqt
wget https://github.com/probonopd/linuxdeployqt/releases/download/6/linuxdeployqt-6-x86_64.AppImage
chmod a+x linuxdeployqt-6-x86_64.AppImage

# Fill with all deps libs and so
./linuxdeployqt-6-x86_64.AppImage $APPDIR/usr/bin/kiwix-desktop -unsupported-allow-new-glibc -bundle-non-qt-libs -extra-plugins=imageformats,iconengines
# Fix the RPATH of QtWebEngineProcess [TODO] Fill a issue ?
patchelf --set-rpath '$ORIGIN/../lib' $APPDIR/usr/libexec/QtWebEngineProcess
patchelf --set-rpath '$ORIGIN/../lib' $APPDIR/usr/bin/kiwix-serve


echo "create $APPDIR/AppRun"
LIBC_BUILD_VERSION=$(ldd --version | head -1 | awk '{ print $NF }')
rm $APPDIR/AppRun
cat <<'EOF' | sed "s/__LIBC_BUILD_VERSION__/${LIBC_BUILD_VERSION}/" > $APPDIR/AppRun
#!/bin/bash

HERE=$(dirname "$(readlink -f "${0}")")
LIBC_VERSION=$(ldd --version | head -1 | awk '{ print $NF }' )
LIBC_BUILD_VERSION="__LIBC_BUILD_VERSION__"

function normalize { printf "%03d%03d" $(echo "$1" | tr '.' ' '); }

if [ $(normalize $LIBC_VERSION) -lt $(normalize $LIBC_BUILD_VERSION) ]
then
  echo "Your glib version ($LIBC_VERSION) is too old to run kiwix-desktop"
  echo "You need at least version $LIBC_BUILD_VERSION."
else
  exec $HERE/usr/bin/kiwix-desktop
fi
EOF
chmod a+x $APPDIR/AppRun
