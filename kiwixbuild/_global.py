from collections import OrderedDict as _OrderedDict

_neutral_env = None
_options = None
_target_steps = _OrderedDict()


def set_neutral_env(env):
    global _neutral_env  # noqa: PLW0603
    _neutral_env = env


def neutral_env(what):
    return getattr(_neutral_env, what)


def set_options(options):
    global _options  # noqa: PLW0603
    _options = options


def option(what):
    return getattr(_options, what)


def add_target_step(key, what):
    _target_steps[key] = what


def get_target_step(key, default_context=None):
    if isinstance(key, tuple):
        context, target = key
    else:
        context, target = default_context, key
    return _target_steps[(context, target)]


def target_steps():
    return _target_steps
