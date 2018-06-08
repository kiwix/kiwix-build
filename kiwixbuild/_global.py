from collections import OrderedDict as _OrderedDict

_neutralEnv = None
_options = None
_target_steps = _OrderedDict()

def set_neutralEnv(env):
    global _neutralEnv
    _neutralEnv = env

def neutralEnv(what):
    return getattr(_neutralEnv, what)

def set_options(options):
    global _options
    _options = options

def option(what):
    return getattr(_options, what)

def add_target_step(key, what):
    _target_steps[key] = what

def get_target_step(key, default_context=None):
    try:
        context, target = key
    except ValueError:
        context, target = default_context, key
    return _target_steps[(context, target)]

def target_steps():
    return _target_steps
