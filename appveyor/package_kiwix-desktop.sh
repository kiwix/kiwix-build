
set -e

NIGHTLY_DATE=$(date +%Y-%m-%d)
NIGHTLY_KIWIX_ARCHIVES_DIR=/c/projects/NIGHTLY_KIWIX_ARCHIVES/${NIGHTLY_DATE}
KIWIX_ARCH_NAME=kiwix-desktop_$NIGHTLY_DATE.zip
KIWIX_DIR=kiwix-desktop_$NIGHTLY_DATE

mkdir $KIWIX_DIR
mkdir -p NIGHTLY_KIWIX_ARCHIVES_DIR

cp /c/projects/kiwix-build/kiwix-desktop/Release/kiwix-desktop.exe $KIWIX_DIR
/c/Qt/5.11/msvc2017_64/bin/windeployqt --compiler-runtime $KIWIX_DIR

cp $MINGW64_EXTRA_DIR/bin/*.dll $KIWIX_DIR

7z a -tzip $NIGHTLY_KIWIX_ARCHIVES_DIR/$KIWIX_ARCH_NAME $KIWIX_DIR
