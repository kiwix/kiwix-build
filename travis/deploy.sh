#!/usr/bin/env bash

set -e

NIGHTLY_KIWIX_ARCHIVES_DIR=${HOME}/NIGHTLY_KIWIX_ARCHIVES/${NIGHTLY_DATE}
NIGHTLY_ZIM_ARCHIVES_DIR=${HOME}/NIGHTLY_ZIM_ARCHIVES/${NIGHTLY_DATE}
RELEASE_KIWIX_ARCHIVES_DIR=${HOME}/RELEASE_KIWIX_ARCHIVES
RELEASE_ZIM_ARCHIVES_DIR=${HOME}/RELEASE_ZIM_ARCHIVES
DIST_KIWIX_ARCHIVES_DIR=${HOME}/DIST_KIWIX_ARCHIVES
DIST_ZIM_ARCHIVES_DIR=${HOME}/DIST_ZIM_ARCHIVES
SSH_KEY=travis/travisci_builder_id_key

if [[ "$TRAVIS_EVENT_TYPE" = "cron" ]]
then
  scp -vrp -i ${SSH_KEY} \
    ${NIGHTLY_KIWIX_ARCHIVES_DIR} \
    nightlybot@download.kiwix.org:/var/www/download.kiwix.org/nightly
  scp -vrp -i ${SSH_KEY} \
    ${NIGHTLY_ZIM_ARCHIVES_DIR} \
    nightlybot@download.kiwix.org:/var/www/download.openzim.org/nightly

elif [[ "x$TRAVIS_TAG" != "x" ]]
then
  RELEASE_ARCHIVES=$(find $RELEASE_KIWIX_ARCHIVES_DIR -type f)
  if [[ "x$RELEASE_ARCHIVES" != "x" ]]
  then
    for archive in $RELEASE_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} \
        ${archive} \
        nightlybot@download.kiwix.org:/var/www/download.kiwix.org/release/${subdir}
    done
  fi

  RELEASE_ARCHIVES=$(find $RELEASE_ZIM_ARCHIVES_DIR -type f)
  if [[ "x$RELEASE_ARCHIVES" != "x" ]]
  then
    for archive in $RELEASE_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} \
        ${archive} \
        nightlybot@download.openzim.org:/var/www/download.openzim.org/release/${subdir}
    done
  fi

  DIST_KIWIX_ARCHIVES=$(find $DIST_KIWIX_ARCHIVES_DIR -type f)
  if [[ "x$DIST_KIWIX_ARCHIVES" != "x" ]]
  then
    for archive in $DIST_KIWIX_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} \
        ${archive} \
        nightlybot@download.kiwix.org:/var/www/download.kiwix.org/release/${subdir}
    done
  fi

  DIST_ZIM_ARCHIVES=$(find $DIST_ZIM_ARCHIVES_DIR -type f)
  if [[ "x$DIST_ZIM_ARCHIVES" != "x" ]]
  then
    for archive in $DIST_ZIM_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} \
        ${archive} \
        nightlybot@download.openzim.org:/var/www/download.openzim.org/release/${subdir}
    done
  fi
fi

