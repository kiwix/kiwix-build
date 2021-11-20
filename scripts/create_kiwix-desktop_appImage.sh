#!/usr/bin/env bash

set -e

INSTALLDIR=${1:-$PWD/BUILD_native_dyn/INSTALL}
SOURCEDIR=${2:-$PWD/SOURCE/kiwix-desktop}
APPDIR=${3:-$PWD/AppDir}

SYSTEMLIBDIR=lib/x86_64-linux-gnu
if [ ! -e "$APPDIR/lib" ] ; then
  SYSTEMLIBDIR=lib64
fi

ICONFILE=$SOURCEDIR/resources/icons/kiwix/scalable/kiwix-desktop.svg
DESKTOPFILE=$SOURCEDIR/resources/org.kiwix.desktop.desktop

# Create structure
mkdir -p $APPDIR/usr/{bin,lib,share} $APPDIR/usr/share/applications $APPDIR/usr/share/icons/hicolor/48x48/apps
# Copy our files
cp $INSTALLDIR/bin/kiwix-desktop $APPDIR/usr/bin/
cp $INSTALLDIR/$SYSTEMLIBDIR/*.so* $APPDIR/usr/lib
# Remove it as it break with linuxdeployqt (should we compile without it) ?
rm -f $APPDIR/usr/lib/libmagic.so*
# Copy nss lib (to not conflict with host's ones)
cp -a /usr/$SYSTEMLIBDIR/nss $APPDIR/usr/lib
cp -a /usr/$SYSTEMLIBDIR/libstdc++.so* $APPDIR/usr/lib
cp -a /usr/$SYSTEMLIBDIR/libc.so* $APPDIR/usr/lib
cp -a /usr/$SYSTEMLIBDIR/libz.so* $APPDIR/usr/lib
cp $ICONFILE $APPDIR/usr/share/icons/hicolor/48x48/apps/kiwix-desktop.svg
mkdir -p $APPDIR/usr/share/applications
cp $DESKTOPFILE $APPDIR/usr/share/applications/kiwix-desktop.desktop

# get the aria2
wget --continue https://github.com/q3aql/aria2-static-builds/releases/download/v1.34.0/aria2-1.34.0-linux-gnu-64bit-build1.tar.bz2
mkdir -p $APPDIR/usr/bin/ && tar -C $APPDIR/usr/bin/ -xf aria2-1.34.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.34.0-linux-gnu-64bit-build1/aria2c --strip-components=1
mkdir -p $APPDIR/etc/ssl/certs/ && tar -C $APPDIR/etc/ssl/certs/ -xf aria2-1.34.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.34.0-linux-gnu-64bit-build1/ca-certificates.crt --strip-components=1

# Get linuxdeployqt
wget --continue https://github.com/probonopd/linuxdeployqt/releases/download/6/linuxdeployqt-6-x86_64.AppImage
chmod a+x linuxdeployqt-6-x86_64.AppImage

# Fill with all deps libs and so
./linuxdeployqt-6-x86_64.AppImage $APPDIR/usr/bin/kiwix-desktop -unsupported-allow-new-glibc -bundle-non-qt-libs -extra-plugins=imageformats,iconengines
# Fix the RPATH of QtWebEngineProcess [TODO] Fill a issue ?
patchelf --set-rpath '$ORIGIN/../lib' $APPDIR/usr/libexec/QtWebEngineProcess
# Build the image.
./linuxdeployqt-6-x86_64.AppImage $APPDIR/usr/share/applications/kiwix-desktop.desktop -unsupported-allow-new-glibc -bundle-non-qt-libs -extra-plugins=imageformats,iconengines -appimage
