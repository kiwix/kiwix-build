set -e

NIGHTLY_DATE=$(date +%Y-%m-%d)
NIGHTLY_KIWIX_ARCHIVES_DIR=/c/projects/NIGHTLY_KIWIX_ARCHIVES/${NIGHTLY_DATE}
SSH_KEY=C:\\projects\\kiwix-build\\appveyor\\nightlybot_id_key

#if [[ "$APPVEYOR_SCHEDULED_BUILD" = "True" ]]
#then
  scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
    ${NIGHTLY_KIWIX_ARCHIVES_DIR} \
    ci@download.kiwix.org:/data/download/nightly
#fi
