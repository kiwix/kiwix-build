from collections import OrderedDict as _OrderedDict
import platform

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
    if isinstance(key, tuple):
        context, target = key
    else:
        context, target = default_context, key
    return _target_steps[(context, target)]


def target_steps():
    return _target_steps


def backend():
    global _backend
    if _backend is not None:
        return _backend

    _platform = platform.system()
    if _platform == "Windows":
        print(
            "ERROR: kiwix-build is not intented to run on Windows platform.\n"
            "There is no backend for Windows, so we can't launch any commands."
        )
        sys.exit(0)
    if _platform == "Linux":
        _platform, _, _ = platform.linux_distribution()
        _platform = _platform.lower()
        _backend = backends.Linux()

    return _backend
