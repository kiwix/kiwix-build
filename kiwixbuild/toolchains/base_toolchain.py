import os
import subprocess

pj = os.path.join

from kiwixbuild.utils import Context, SkipCommand, StopBuild
from kiwixbuild._global import neutralEnv

class _MetaToolchain(type):
    def __new__(cls, name, bases, dct):
        _class = type.__new__(cls, name, bases, dct)
        if name != 'Toolchain':
            Toolchain.all_toolchains[dct['name']] = _class
        return _class


class Toolchain(metaclass=_MetaToolchain):
    force_native_build = False
    neutral = True
    all_toolchains = {}
    configure_option = ""
    cmake_option = ""
    exec_wrapper_def = ""
    Builder = None
    Source = None


    @classmethod
    def full_name(cls):
        return "{name}-{version}".format(
            name = cls.name,
            version = cls.version)

    @property
    def source_path(self):
        return pj(neutralEnv('source_dir'), self.source.source_dir)

    @property
    def _log_dir(self):
        return neutralEnv('log_dir')

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
