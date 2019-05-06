#!/usr/bin/env bash

set -e

EXPORT_DIR=${HOME}/EXPORT
NIGHTLY_KIWIX_ARCHIVES_DIR=${EXPORT_DIR}/NIGHTLY_KIWIX_ARCHIVES/${NIGHTLY_DATE}
NIGHTLY_ZIM_ARCHIVES_DIR=${EXPORT_DIR}/NIGHTLY_ZIM_ARCHIVES/${NIGHTLY_DATE}
RELEASE_KIWIX_ARCHIVES_DIR=${EXPORT_DIR}/RELEASE_KIWIX_ARCHIVES
RELEASE_ZIM_ARCHIVES_DIR=${EXPORT_DIR}/RELEASE_ZIM_ARCHIVES
DIST_KIWIX_ARCHIVES_DIR=${EXPORT_DIR}/DIST_KIWIX_ARCHIVES
DIST_ZIM_ARCHIVES_DIR=${EXPORT_DIR}/DIST_ZIM_ARCHIVES

if [[ "$TRAVIS_EVENT_TYPE" = "cron" ]]
then
  scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
    ${NIGHTLY_KIWIX_ARCHIVES_DIR} \
    ci@download.kiwix.org:/data/download/nightly
  scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
    ${NIGHTLY_ZIM_ARCHIVES_DIR} \
    ci@download.openzim.org:/data/openzim/nightly

elif [[ "x$TRAVIS_TAG" != "x" ]]
then
  RELEASE_ARCHIVES=$(find $RELEASE_KIWIX_ARCHIVES_DIR -type f)
  if [[ "x$RELEASE_ARCHIVES" != "x" ]]
  then
    for archive in $RELEASE_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
        ${archive} \
        ci@download.kiwix.org:/data/download/release/${subdir}
    done
  fi

  RELEASE_ARCHIVES=$(find $RELEASE_ZIM_ARCHIVES_DIR -type f)
  if [[ "x$RELEASE_ARCHIVES" != "x" ]]
  then
    for archive in $RELEASE_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
        ${archive} \
        ci@download.openzim.org:/data/openzim/release/${subdir}
    done
  fi

  DIST_KIWIX_ARCHIVES=$(find $DIST_KIWIX_ARCHIVES_DIR -type f)
  if [[ "x$DIST_KIWIX_ARCHIVES" != "x" ]]
  then
    for archive in $DIST_KIWIX_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
        ${archive} \
        ci@download.kiwix.org:/data/download/release/${subdir}
    done
  fi

  DIST_ZIM_ARCHIVES=$(find $DIST_ZIM_ARCHIVES_DIR -type f)
  if [[ "x$DIST_ZIM_ARCHIVES" != "x" ]]
  then
    for archive in $DIST_ZIM_ARCHIVES
    do
      subdir=$(basename $(dirname $archive))
      scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
        ${archive} \
        ci@download.openzim.org:/data/openzim/release/${subdir}
    done
  fi

  GIT_REPOS=$(ls -d */)
  if [[ "x$GIT_REPOS" != "x" ]]
  then
    for repo in $GIT_REPOS
    do
      (cd repo;
      GIT_SSH_COMMAND"ssh -o StrictHostKeyChecking=no -i $SSH_KEY" git push
      )
    done
  fi
fi

