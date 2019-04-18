#!/usr/bin/env bash

set -e

BASE_EXPORT_DIR=$HOME/EXPORT/BASE
ls $BASE_EXPORT_DIR

BASE_ARCHIVES=$(find $BASE_EXPORT_DIR -type f)
echo $BASE_ARCHIVES
if [[ "x$BASE_ARCHIVES" != "x" ]]
then
  scp -vrp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
    $BASE_ARCHIVES \
    ci@tmp.kiwix.org:/data/tmp/ci
fi
