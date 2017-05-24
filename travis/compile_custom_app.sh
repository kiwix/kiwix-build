#!/usr/bin/env bash

set -e

cd ${HOME}

${TRAVIS_BUILD_DIR}/kiwix-build.py \
  --target-platform $PLATFORM \
  --hide-progress \
  --android-custom-app $CUSTOM_APP \
  --zim-file-size $ZIM_FILE_SIZE \
  kiwix-android-custom

