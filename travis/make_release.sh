#!/usr/bin/env bash

set -e

KEYSTORE_FILE=${TRAVIS_BUILD_DIR}/travis/test_ks.ks
GOOGLE_API_KEY=${TRAVIS_BUILD_DIR}/travis/googleplay_android_developer-5a411156212c.json
SSH_KEY=${TRAVIS_BUILD_DIR}/travis/travisci_builder_id_key

cd ${HOME}


BASE_DIR="BUILD_${PLATFORM}"

mkdir -p ${HOME}/APKS

scp -i ${SSH_KEY} nightlybot@download.kiwix.org:${DEPLOY_DIR}/* ${HOME}/APKS

ssh -i ${SSH_KEY} nightlybot@download.kiwix.org "rm -rf ${DEPLOY_DIR}"

${TRAVIS_BUILD_DIR}/build_custom_app.py \
  --step publish \
  --custom-app ${CUSTOM_APP} \
  --package-name ${PACKAGE_NAME} \
  --google-api-key ${GOOGLE_API_KEY} \
  --zim-url ${ZIM_URL} \
  --apks-dir ${HOME}/APKS \
  --content-version-code ${CONTENT_VERSION_CODE}
