# `ConfigInfo` must be defined before the config modules register themselves.
from .base import ConfigInfo

# isort: split
from . import (  # noqa: F401 (imported to register the configs)
    android,
    apple,
    armhf,
    flatpak,
    i586,
    musl,
    native,
    neutral,
    wasm,
)

__all__ = ["ConfigInfo"]
