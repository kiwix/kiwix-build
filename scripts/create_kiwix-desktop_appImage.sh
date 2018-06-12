#!/usr/bin/env bash

set -e

INSTALLDIR=${1:-$PWD/BUILD_native_dyn/INSTALL}
APPDIR=${2:-$PWD/AppDir}

#TODO We should have our icon
ICONFILE=/usr/share/icons/hicolor/48x48/apps/gvim.png

# Create structure
mkdir -p $APPDIR/usr/{bin,lib,share} $APPDIR/usr/share/applications $APPDIR/usr/share/icons/hicolor/48x48/apps
# Copy our files
cp $INSTALLDIR/bin/kiwix-desktop $APPDIR/usr/bin/
cp $INSTALLDIR/lib/x86_64-linux-gnu/*.so* $APPDIR/usr/lib
# Remove it as it break with linuxdeployqt (should we compile without it) ?
rm $APPDIR/usr/lib/libmagic.so*
# Copy nss lib (to not conflict with host's ones)
cp -a /usr/lib/x86_64-linux-gnu/nss $APPDIR/usr/lib
cp $ICONFILE $APPDIR/usr/share/icons/hicolor/48x48/apps/kiwix-desktop.png
# TODO we should have our .desktop
tee $APPDIR/usr/share/applications/kiwix-desktop.desktop <<EOF > /dev/null
[Desktop Entry]
Name=Kiwix
Exec=kiwix-desktop %F
Icon=kiwix-desktop
Type=Application
Terminal=false
StartupNotify=true
NoDisplay=false
EOF

# Get linuxdeployqt
wget https://github.com/probonopd/linuxdeployqt/releases/download/continuous/linuxdeployqt-continuous-x86_64.AppImage
chmod a+x linuxdeployqt-continuous-x86_64.AppImage

# Fill with all deps libs and so
./linuxdeployqt-continuous-x86_64.AppImage $APPDIR/usr/bin/kiwix-desktop -verbose=3 -bundle-non-qt-libs
# Fix the RPATH of QtWebEngineProcess [TODO] Fill a issue ?
patchelf --set-rpath '$ORIGIN/../lib' $APPDIR/usr/libexec/QtWebEngineProcess
# Build the image.
./linuxdeployqt-continuous-x86_64.AppImage $APPDIR/usr/share/applications/kiwix-desktop.desktop -verbose=3 -bundle-non-qt-libs -appimage   #
