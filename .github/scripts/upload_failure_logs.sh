#!/usr/bin/env bash

set -e

cd $HOME

ARCHIVE_NAME=fail_log_${OS_NAME}_${PLATFORM_TARGET}.tar.gz
TO_ARCHIVE="$HOME/BUILD_* $HOME/SOURCE $HOME/LOGS $HOME/TOOLCHAINS"
if [[ "$OS_NAME" == "osx" ]]
then
  TO_ARCHIVE="$TO_ARCHIVE $(xcrun --sdk iphoneos --show-sdk-path)"
fi
echo $TO_ARCHIVE
tar -czhf ${ARCHIVE_NAME} $TO_ARCHIVE

echo "Uploading archive $ARCHIVE_NAME"

scp -p -i ${SSH_KEY} \
  -o PasswordAuthentication=no \
  -o StrictHostKeyChecking=no \
  $ARCHIVE_NAME \
  ci@tmp.kiwix.org:/data/tmp/ci
