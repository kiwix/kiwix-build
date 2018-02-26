#!/usr/bin/env bash

set -e

NIGHTLY_ARCHIVES_DIR=${HOME}/NIGHTLY_ARCHIVES
RELEASE_ARCHIVES_DIR=${HOME}/RELEASE_ARCHIVES
DIST_KIWIX_ARCHIVES_DIR=${HOME}/DIST_KIWIX_ARCHIVES
DIST_ZIM_ARCHIVES_DIR=${HOME}/DIST_ZIM_ARCHIVES
SSH_KEY=travis/travisci_builder_id_key

if [[ "$TRAVIS_EVENT_TYPE" = "cron" ]]
then
  NIGHTLY_ARCHIVES=$(find $NIGHTLY_ARCHIVES_DIR -type f)
  if [[ "x$NIGHTLY_ARCHIVES" != "x" ]]
  then
    scp -vrp -i ${SSH_KEY} \
      ${NIGHTLY_ARCHIVES} \
      nightlybot@download.kiwix.org:/var/www/download.kiwix.org/nightly/$(date +%Y-%m-%d)
  fi
elif [[ "x$TRAVIS_TAG" != "x" ]]
then
  RELEASE_ARCHIVES=$(find $RELEASE_ARCHIVES_DIR -type f)
  if [[ "x$RELEASE_ARCHIVES" != "x" ]]
  then
    scp -vrp -i ${SSH_KEY} \
      ${RELEASE_ARCHIVES} \
      nightlybot@download.kiwix.org:/var/www/download.kiwix.org/release
  fi

  DIST_KIWIX_ARCHIVES=$(find $DIST_KIWIX_ARCHIVES_DIR -type f)
  if [[ "x$DIST_KIWIX_ARCHIVES" != "x" ]]
  then
    scp -vrp -i ${SSH_KEY} \
      ${DIST_KIWIX_ARCHIVES} \
      nightlybot@download.kiwix.org:/var/www/download.kiwix.org/release
  fi

  DIST_ZIM_ARCHIVES=$(find $DIST_ZIM_ARCHIVES_DIR -type f)
  if [[ "x$DIST_ZIM_ARCHIVES" != "x" ]]
  then
    scp -vrp -i ${SSH_KEY} \
      ${DIST_ZIM_ARCHIVES} \
      nightlybot@download.openzim.org:/var/www/download.openzim.org/release
  fi
fi

