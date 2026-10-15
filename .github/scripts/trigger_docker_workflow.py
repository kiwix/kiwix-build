#!/usr/bin/env python3

from build_definition import DOCKER, select_build_targets
from common import (
    MAKE_RELEASE,
    trigger_docker_publish,
)

# Filter what to build if we are doing a release.
if MAKE_RELEASE:
    docker_trigger = select_build_targets(DOCKER)
else:
    docker_trigger = []

for target in docker_trigger:
    trigger_docker_publish(target)
