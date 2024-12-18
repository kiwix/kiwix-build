#!/usr/bin/env bash

set -e

INSTALLDIR=${1:-$PWD/BUILD_native_dyn/INSTALL}
SOURCEDIR=${2:-$PWD/SOURCE/kiwix-desktop}
APPDIR=${3:-$PWD/AppDir}

SYSTEMLIBDIR=lib/x86_64-linux-gnu
if [ ! -e "$INSTALLDIR/lib" ] ; then
  SYSTEMLIBDIR=lib64
fi

ICONFILE=$SOURCEDIR/resources/icons/kiwix/scalable/kiwix-desktop.svg
DESKTOPFILE=$SOURCEDIR/resources/org.kiwix.desktop.desktop

# Get linuxdeploy
wget --continue https://github.com/linuxdeploy/linuxdeploy/releases/download/1-alpha-20240109-1/linuxdeploy-x86_64.AppImage
chmod u+x linuxdeploy-x86_64.AppImage
wget --continue https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/1-alpha-20240109-1/linuxdeploy-plugin-qt-x86_64.AppImage
chmod u+x linuxdeploy-plugin-qt-x86_64.AppImage

# Fill with all deps libs and so
LD_LIBRARY_PATH=$INSTALLDIR/lib/x86_64-linux-gnu ./linuxdeploy-x86_64.AppImage \
    --plugin=qt \
    --appdir="$APPDIR" \
    --executable=$INSTALLDIR/bin/kiwix-desktop \
    --desktop-file=$DESKTOPFILE \
    --icon-file=$ICONFILE \
    --library=/usr/lib/x86_64-linux-gnu/libthai.so.0 \

# get the aria2
wget --continue https://dev.kiwix.org/kiwix-desktop/aria2-1.36.0-linux-gnu-64bit-build1.tar.bz2
mkdir -p $APPDIR/usr/bin/ && tar -C $APPDIR/usr/bin/ -xf aria2-1.36.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.36.0-linux-gnu-64bit-build1/aria2c --strip-components=1
mkdir -p $APPDIR/etc/ssl/certs/ && tar -C $APPDIR/etc/ssl/certs/ -xf aria2-1.36.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.36.0-linux-gnu-64bit-build1/ca-certificates.crt --strip-components=1

# Fix the RPATH of QtWebEngineProcess [TODO] Fill a issue ?
patchelf --set-rpath '$ORIGIN/../lib' $APPDIR/usr/libexec/QtWebEngineProcess

mv $APPDIR/{AppRun.wrapped,kiwix-desktop}
sed -i 's/AppRun\.wrapped/kiwix-desktop/g' $APPDIR/AppRun
wget --continue https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage
chmod u+x appimagetool-x86_64.AppImage

./appimagetool-x86_64.AppImage AppDir Kiwix-"$VERSION"-x86_64.AppImage
