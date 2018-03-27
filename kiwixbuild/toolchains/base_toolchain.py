import os
import subprocess

pj = os.path.join

from kiwixbuild.utils import Context, SkipCommand, StopBuild

class _MetaToolchain(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name != 'Toolchain':
            Toolchain.all_toolchains[name] = _class
        return _class


class Toolchain(metaclass=_MetaToolchain):
    all_toolchains = {}
    configure_option = ""
    cmake_option = ""
    exec_wrapper_def = ""
    Builder = None
    Source = None

    def __init__(self, buildEnv):
        self.buildEnv = buildEnv
        self.source = self.Source(self) if self.Source else None
        self.builder = self.Builder(self) if self.Builder else None

    @property
    def full_name(self):
        return "{name}-{version}".format(
            name = self.name,
            version = self.version)

    @property
    def source_path(self):
        return pj(self.buildEnv.source_dir, self.source.source_dir)

    @property
    def _log_dir(self):
        return self.buildEnv.log_dir

    def set_env(self, env):
        pass

    def set_compiler(self, env):
        pass

    def command(self, name, function, *args):
        print("  {} {} : ".format(name, self.name), end="", flush=True)
        log = pj(self._log_dir, 'cmd_{}_{}.log'.format(name, self.name))
        context = Context(name, log, True)
        try:
            ret = function(*args, context=context)
            context._finalise()
            print("OK")
            return ret
        except SkipCommand:
            print("SKIP")
        except subprocess.CalledProcessError:
            print("ERROR")
            try:
                with open(log, 'r') as f:
                    print(f.read())
            except:
                pass
            raise StopBuild()
        except:
            print("ERROR")
            raise
