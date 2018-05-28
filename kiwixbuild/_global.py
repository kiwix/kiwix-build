_neutralEnv = None

def set_neutralEnv(env):
    global _neutralEnv
    _neutralEnv = env

def neutralEnv(what):
    return getattr(_neutralEnv, what)
