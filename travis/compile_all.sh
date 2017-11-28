#!/usr/bin/env bash

set -e

BASE_DIR="BUILD_${PLATFORM}"
NIGHTLY_ARCHIVES_DIR=${HOME}/NIGHTLY_ARCHIVES
RELEASE_ARCHIVES_DIR=${HOME}/RELEASE_ARCHIVES
SSH_KEY=${TRAVIS_BUILD_DIR}/travis/travisci_builder_id_key

mkdir -p ${NIGHTLY_ARCHIVES_DIR}
mkdir -p ${RELEASE_ARCHIVES_DIR}

function make_archive {
  if [[ "$MAKE_RELEASE" == "0" ]]
  then
    ARCHIVE_PATH="${NIGHTLY_ARCHIVES_DIR}/${1}_$(date +%Y-%m-%d).tar.gz"
  else
    ARCHIVE_PATH="${RELEASE_ARCHIVES_DIR}/${1}-${TRAVIS_TAG}.tar.gz"
  fi
  (
    cd ${BASE_DIR}/INSTALL/bin
    tar -czf "${ARCHIVE_PATH}" $2
  )
}

cd ${HOME}

if [[ $TRAVIS_TAG =~ ^[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+ ]]
then
   MAKE_RELEASE=1
else
   MAKE_RELEASE=0
fi

if [[ "$TRAVIS_EVENT_TYPE" == "cron" || "$MAKE_RELEASE" == "1" ]]
then
  if [[ ${PLATFORM} = android* ]]
  then
    TARGETS="libzim kiwix-lib kiwix-android"
  elif [[ ${PLATFORM} =~ native_* ]]
  then
    TARGETS="libzim zimwriterfs zim-tools kiwix-lib kiwix-tools"
  else
    TARGETS="libzim kiwix-lib kiwix-tools"
  fi

  for TARGET in ${TARGETS}
  do
    echo $TARGET
    if [[ "$TRAVIS_EVENT_TYPE" == "cron" ]]
    then
      ${TRAVIS_BUILD_DIR}/kiwix-build.py \
        --target-platform $PLATFORM \
        --build-deps-only \
        --hide-progress \
        ${TARGET}
      rm ${BASE_DIR}/.install_packages_ok

      (
        cd ${BASE_DIR}
        if [ -f meson_cross_file.txt ]
        then
          MESON_FILE=meson_cross_file.txt
        fi
        ANDROID_NDK_DIR=$(find . -name "android-ndk*")
        ARCHIVE_NAME="deps_${PLATFORM}_${TARGET}.tar.gz"

        cat <<EOF > manifest.txt
${ARCHIVE_NAME}
*********************************

Dependencies archive for ${TARGET} on platform ${PLATFORM}
Generated at $(date)
EOF

        tar -czf ${ARCHIVE_NAME} INSTALL manifest.txt ${MESON_FILE} ${ANDROID_NDK_DIR}
        scp -i ${SSH_KEY} ${ARCHIVE_NAME} nightlybot@download.kiwix.org:/var/www/tmp.kiwix.org/ci/
      )
    fi

    if [[ "$MAKE_RELEASE" == "1" ]]
    then
        ${TRAVIS_BUILD_DIR}/kiwix-build.py \
            --hide-progress \
            --make-release \
            --target-platform $PLATFORM ${TARGET}
    else
        ${TRAVIS_BUILD_DIR}/kiwix-build.py \
            --hide-progress \
            --target-platform $PLATFORM ${TARGET}
    fi
    rm ${BASE_DIR}/.install_packages_ok
  done

  # We have build every thing. Now create archives for public deployement.
  case ${PLATFORM} in
    native_static)
      make_archive kiwix_tools_linux64 "kiwix-install kiwix-manage kiwix-read kiwix-search kiwix-serve"
      make_archive zim-tools_linux64 "zimbench zimdump zimsearch zimdiff zimpatch zimsplit"
      make_archive zimwriterfs_linux64 "zimwriterfs"
      ;;
    win32_static)
      make_archive kiwix-tools_win32 "kiwix-install.exe kiwix-manage.exe kiwix-read.exe kiwix-search.exe kiwix-serve.exe"
      ;;
    armhf_static)
      make_archive kiwix-tools_armhf "kiwix-install kiwix-manage kiwix-read kiwix-search kiwix-serve"
      ;;
    android_*)
      APK_NAME="kiwix-${PLATFORM}"
      cp ${BASE_DIR}/kiwix-android/app/build/outputs/apk/app-kiwix-debug.apk ${NIGHTLY_ARCHIVES_DIR}/${APK_NAME}-debug.apk
      cp ${BASE_DIR}/kiwix-android/app/build/outputs/apk/app-kiwix-release-unsigned.apk ${NIGHTLY_ARCHIVES_DIR}/${APK_NAME}-release-unsigned.apk
      ;;
  esac

else
  # No a cron job, we just have to build to be sure nothing is broken.
  if [[ ${PLATFORM} = android* ]]
  then
    TARGETS="kiwix-android"
  elif [[ ${PLATFORM} =~ native_* ]]
  then
    TARGETS="kiwix-tools zim-tools zimwriterfs"
  else
    TARGETS="kiwix-tools"
  fi
  for TARGET in ${TARGETS}
  do
    ${TRAVIS_BUILD_DIR}/kiwix-build.py \
      --target-platform $PLATFORM \
      --hide-progress \
      ${TARGET}
  done
fi
