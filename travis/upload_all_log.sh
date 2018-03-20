#!/usr/bin/env bash

set -e

SSH_KEY=$(pwd)/travis/travisci_builder_id_key

cd $HOME

tar -czf fail_log_${PLATFORM}.tar.gz BUILD_${PLATFORM}

scp -vrp -i ${SSH_KEY} \
  fail_log_${PLATFORM}.tar.gz \
  nightlybot@download.kiwix.org:/var/www/tmp.kiwix.org/ci
