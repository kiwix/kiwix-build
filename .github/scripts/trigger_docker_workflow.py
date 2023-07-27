#!/usr/bin/env python3

from common import (
    trigger_docker_publish,
    MAKE_RELEASE,
)

from build_definition import select_build_targets, DOCKER

# Filter what to build if we are doing a release.
if MAKE_RELEASE:
    docker_trigger = select_build_targets(DOCKER)
else:
    docker_trigger = []

for target in docker_trigger:
    trigger_docker_publish(target)
