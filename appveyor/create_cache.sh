
set -e

ARCHIVE_NAME="deps_windows_windows.zip"
SSH_KEY=C:\\projects\\kiwix-build\\appveyor\\nightlybot_id_key

7z a -tzip $ARCHIVE_NAME $MINGW64_EXTRA_DIR
scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
  ${ARCHIVE_NAME} \
  ci@tmp.kiwix.org:/data/tmp/ci

