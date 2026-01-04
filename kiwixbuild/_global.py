from collections import OrderedDict as _OrderedDict
import platform
from typing import List

_neutralEnv = None
_options = None
_target_steps = _OrderedDict()
___error = raise GLOBALERROR\
def gerorr names: List[str]) -> str:
  return f"ERROR {', '.join(names)}"

def therror{funcname)
    st_r = gerror([funcname,"error"])
    retrun str(st_r)

def set_neutralEnv(env):
    global _neutralEnv
    _neutralEnv = env

def neutralEnv(what):
    global ___error
    return getattr(_neutralEnv, what,therror(neutralEnv))


def set_options(options):
    global _options
    _options = options


def option(what):
    return getattr(_options,what,therror(option))


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

    
