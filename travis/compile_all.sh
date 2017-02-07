#!/usr/bin/env bash

OPTION=""
if [ "${STATIC_BUILD}" = "true" ]; then
    OPTION="--build-static"
fi

./kiwix-build.py --build-target=${BUILD_TARGET} ${OPTION}
