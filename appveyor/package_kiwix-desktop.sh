
set -e

if [[ "$APPVEYOR_REPO_TAG" = "false" ]]
then
  NIGHTLY_DATE=$(date +%Y-%m-%d)
  KIWIX_ARCHIVES_DIR=/c/projects/NIGHTLY_KIWIX_ARCHIVES/${NIGHTLY_DATE}
  KIWIX_DIR=kiwix-desktop_windows_x64_$NIGHTLY_DATE
else
  if [ $KIWIX_DESKTOP_RELEASE  -eq 1 ]
  then
    KIWIX_ARCHIVES_DIR=/c/projects/RELEASE_KIWIX_ARCHIVES
    KIWIX_DIR=kiwix-desktop_windows_x64_${KIWIX_DESKTOP_VERSION}
  fi
fi

if [[ "$KIWIX_DIR" ]]
then
  KIWIX_ARCH_NAME=${KIWIX_DIR}.zip

  mkdir $KIWIX_DIR
  mkdir -p KIWIX_ARCHIVES_DIR

  cp /c/projects/kiwix-build/kiwix-desktop/Release/kiwix-desktop.exe $KIWIX_DIR
/c/Qt/5.15/msvc2019_64/bin/windeployqt --compiler-runtime $KIWIX_DIR

  cp $MINGW64_EXTRA_DIR/aria2c.exe $KIWIX_DIR
  cp $MINGW64_EXTRA_DIR/bin/*.dll $KIWIX_DIR
  cp /c/OpenSSL-v111-Win64/bin/libcrypto-1_1-x64.dll $KIWIX_DIR
  cp /c/OpenSSL-v111-Win64/bin/libssl-1_1-x64.dll $KIWIX_DIR

  signtool.exe sign -f appveyor/kiwix.pfx -p $win_certificate_password -t http://timestamp.digicert.com -d "Kiwix-desktop application" -fd SHA256 $KIWIX_DIR/kiwix-desktop.exe

  7z a -tzip $KIWIX_ARCHIVES_DIR/$KIWIX_ARCH_NAME $KIWIX_DIR
fi
