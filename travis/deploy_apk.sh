#!/usr/bin/env bash

set -e

KEYSTORE_FILE=${TRAVIS_BUILD_DIR}/travis/test_ks.ks
GOOGLE_API_KEY=${TRAVIS_BUILD_DIR}/travis/googleplay_android_developer-5a411156212c.json
SSH_KEY=${TRAVIS_BUILD_DIR}/travis/travisci_builder_id_key

cd ${HOME}

# Sign apk file

BASE_DIR="BUILD_${PLATFORM}"
INPUT_APK_FILE=${BASE_DIR}/kiwix-android-custom_${CUSTOM_APP}/app/build/outputs/apk/app-${CUSTOM_APP}-release-unsigned.apk
SIGNED_APK=${BASE_DIR}/app-${CUSTOM_APP}_${VERSION_CODE}-release-signed.apk

TOOLCHAINS/android-sdk-r25.2.3/build-tools/25.0.2/apksigner sign \
  --ks ${KEYSTORE_FILE} \
  --ks-pass env:KEYSTORE_PASS \
  --out ${SIGNED_APK} \
  ${INPUT_APK_FILE}

ssh -i ${SSH_KEY} nightlybot@download.kiwix.org "mkdir -p ~/apks/${CUSTOM_APP}_${BASE_VERSION}"

scp -i ${SSH_KEY} \
  ${SIGNED_APK} \
  nightlybot@download.kiwix.org:~/apks/${CUSTOM_APP}_${BASE_VERSION}
