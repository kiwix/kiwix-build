


class PlatformInfo:
    all_platforms = {}

    def __init__(self, name, build, static, toolchains, hosts=None):
        self.all_platforms[name] = self
        self.build = build
        self.static = static
        self.toolchains = toolchains
        self.compatible_hosts = hosts

    def __str__(self):
        return "{}_{}".format(self.build, 'static' if self.static else 'dyn')

    def set_env(self, env):
        pass

    def get_bind_dir(self):
        return []
