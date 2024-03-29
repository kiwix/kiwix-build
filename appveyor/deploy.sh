set -e

NIGHTLY_DATE=$(date +%Y-%m-%d)
NIGHTLY_KIWIX_ARCHIVES_DIR=/c/projects/NIGHTLY_KIWIX_ARCHIVES/${NIGHTLY_DATE}
RELEASE_KIWIX_ARCHIVES_DIR=/c/projects/RELEASE_KIWIX_ARCHIVES
SSH_KEY=C:\\projects\\kiwix-build\\appveyor\\nightlybot_id_key

if [[ "$APPVEYOR_SCHEDULED_BUILD" = "True" ]]
then
  scp -P 30022 -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
    ${NIGHTLY_KIWIX_ARCHIVES_DIR} \
    ci@master.download.kiwix.org:/data/download/nightly
fi

if [[ "$APPVEYOR_REPO_TAG" = "true" ]]
then
  RELEASE_ARCHIVES=$(find $RELEASE_KIWIX_ARCHIVES_DIR -type f)
  scp -P 30022 -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
      ${RELEASE_ARCHIVES} \
      ci@master.download.kiwix.org:/data/download/release/kiwix-desktop
fi
