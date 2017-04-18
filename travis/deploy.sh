#!/usr/bin/env bash

set -e

NIGHTLY_ARCHIVES_DIR=${HOME}/NIGHTLY_ARCHIVES
SSH_KEY=travis/travisci_builder_id_key

NIGHTLY_ARCHIVES=$(find $NIGHTLY_ARCHIVES_DIR -type f)
if [[ "x$NIGHTLY_ARCHIVES" != "x" ]]
then
  scp -vrp -i ${SSH_KEY} \
    ${NIGHTLY_ARCHIVES} \
    nightlybot@download.kiwix.org:/var/www/download.kiwix.org/nightly/$(date +%Y-%m-%d)
fi
