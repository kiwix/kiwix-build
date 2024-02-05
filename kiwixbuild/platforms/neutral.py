from .base import PlatformInfo


class NeutralPlatformInfo(PlatformInfo):
    name = "neutral"
    static = ""
    compatible_hosts = ["fedora", "debian", "Darwin"]

    def __str__(self):
        return "neutral"
