#!/usr/bin/env bash

set -e

APPDIR=${1:-$PWD/AppDir}
APPIMAGETOOL=appimagetool-x86_64.AppImage
VERSION=$(grep '^VERSION' $APPDIR/info.txt | awk '{print $2}')
EXPORT_DIR=$(grep '^EXPORT_DIR' $APPDIR/info.txt | awk '{print $2}')
APP_NAME="kiwix-desktop_x86_64_${VERSION}.appimage"

# Get linuxdeployqt
if [ ! -x $APPIMAGETOOL ]
then
  wget https://github.com/AppImage/AppImageKit/releases/download/12/$APPIMAGETOOL
  chmod a+x $APPIMAGETOOL
fi

echo "Create appimage from $APPDIR to ${EXPORT_DIR}/$APP_NAME"
# Build the image.
./$APPIMAGETOOL $APPDIR $EXPORT_DIR/$APP_NAME
