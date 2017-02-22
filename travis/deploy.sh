#!/usr/bin/env bash

set -e

SSH_KEY=travis/travisci_builder_id_key

chmod 600 ${SSH_KEY}

BASE_DIR="BUILD_*/INSTALL"
./kiwix-deploy.py ${BASE_DIR} ${ARCHIVE_TYPE} \
    --deploy \
    --ssh_private_key=${SSH_KEY} \
    --server=nightlybot@download.kiwix.org \
    --base_path=/var/www/download.kiwix.org/nightly
