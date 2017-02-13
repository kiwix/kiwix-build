#!/usr/bin/env bash

set -e

SSH_KEY=travis/travisci_builder_id_key

chmod 600 ${SSH_KEY}


BASE_DIR="BUILD_${BUILD_TARGET}_static/INSTALL"
if [ "${BUILD_TARGET}" = "win32" ]; then
    ARCHIVE_OPTION="--zip"
else
    ARCHIVE_OPTION="--tar"
fi
./kiwix-deploy.py ${BASE_DIR} ${ARCHIVE_OPTION} \
    --deploy \
    --ssh_private_key=${SSH_KEY} \
    --server=nightlybot@download.kiwix.org \
    --base_path=/var/www/download.kiwix.org/nightly
