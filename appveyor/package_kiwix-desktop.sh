
set -e

if [[ "$APPVEYOR_REPO_TAG" = "false" ]]
then
  NIGHTLY_DATE=$(date +%Y-%m-%d)
  KIWIX_ARCHIVES_DIR=/c/projects/NIGHTLY_KIWIX_ARCHIVES/${NIGHTLY_DATE}
  KIWIX_DIR=kiwix-desktop_windows_x64_$NIGHTLY_DATE
else
  KIWIX_DESKTOP_VERSION=2.0-beta5
  KIWIX_ARCHIVES_DIR=/c/projects/RELEASE_KIWIX_ARCHIVES
  KIWIX_DIR=kiwix-desktop_windows_x64_${KIWIX_DESKTOP_VERSION}
fi

KIWIX_ARCH_NAME=${KIWIX_DIR}.zip

mkdir $KIWIX_DIR
mkdir -p KIWIX_ARCHIVES_DIR

cp /c/projects/kiwix-build/kiwix-desktop/Release/kiwix-desktop.exe $KIWIX_DIR
/c/Qt/5.11/msvc2017_64/bin/windeployqt --compiler-runtime $KIWIX_DIR

cp $MINGW64_EXTRA_DIR/aria2c.exe $KIWIX_DIR
cp $MINGW64_EXTRA_DIR/bin/*.dll $KIWIX_DIR

/c/Program\ Files\ \(x86\)/Windows\ Kits/10/bin/x64/signtool.exe sign -f appveyor/kiwix.pfx -p $win_certificate_password -t http://timestamp.verisign.com/scripts/timestamp.dll -d "Kiwix-desktop application" $KIWIX_DIR/kiwix-desktop.exe

7z a -tzip $KIWIX_ARCHIVES_DIR/$KIWIX_ARCH_NAME $KIWIX_DIR
