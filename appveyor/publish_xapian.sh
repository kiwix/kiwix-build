
set -e

KIWIX_ARCHIVES_DIR=/c/projects/BUILD_ARCHIVES
KIWIX_DIR="/c/extra"
SSH_KEY=C:\\projects\\kiwix-build\\appveyor\\nightlybot_id_key

KIWIX_ARCH_NAME=build_dir.zip

mkdir -p KIWIX_ARCHIVES_DIR

7z a -tzip $KIWIX_ARCHIVES_DIR/$KIWIX_ARCH_NAME $KIWIX_DIR


scp -P 30022 -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
  $KIWIX_ARCHIVES_DIR/$KIWIX_ARCH_NAME \
  ci@master.download.kiwix.org:/data/tmp/ci/dev_preview

