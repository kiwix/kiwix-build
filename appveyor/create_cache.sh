
set -e

ARCHIVE_NAME="deps_windows_windows.zip"
SSH_KEY=C:\\projects\\kiwix-build\\appveyor\\nightlybot_id_key

7z a -tzip $ARCHIVE_NAME $MINGW64_EXTRA_DIR
scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
  ${ARCHIVE_NAME} \
  nightlybot@download.kiwix.org:/var/www/tmp.kiwix.org/ci

