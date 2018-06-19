from .base import (
    Dependency,
    ReleaseDownload,
    CMakeBuilder)

from kiwixbuild.utils import Remotefile, pj, run_command
from glob import glob

class CTPP2(Dependency):
    name = "ctpp2"

    class Source(ReleaseDownload):
        name = "ctpp2"
        source_dir = "ctpp2-2.8.3"
        archive = Remotefile('ctpp2-2.8.3.tar.gz',
                             'a83ffd07817adb575295ef40fbf759892512e5a63059c520f9062d9ab8fb42fc')
        patches = ["ctpp2_include.patch",
                   "ctpp2_no_src_modification.patch",
                   "ctpp2_fix-static-libname.patch",
                   "ctpp2_mingw32.patch",
                   "ctpp2_dll_export_VMExecutable.patch",
                   "ctpp2_win_install_lib_in_lib_dir.patch",
                   "ctpp2_iconv_support.patch",
                   "ctpp2_compile_ctpp2c_static.patch",
                  ]

    class Builder(CMakeBuilder):
        @property
        def configure_options(self):
            yield "-DMD5_SUPPORT=OFF"
            yield "-DICONV_SUPPORT=OFF"
            libprefix = self.buildEnv.libprefix
            if libprefix.startswith('lib'):
               libprefix = libprefix[3:]
               yield "-DLIB_SUFFIX={}".format(libprefix)


class CTPP2C(CTPP2):
    name = "ctpp2c"
    force_native_build = True

    class Builder(CTPP2.Builder):
        make_targets = ["ctpp2c"]

        @property
        def build_path(self):
            return super().build_path+"_native"

        def _install(self, context):
            context.try_skip(self.build_path)
            command = (
                'cp',
                *glob(pj(self.build_path, 'ctpp2c*')),
                pj(self.buildEnv.install_dir, 'bin')
            )
            run_command(command, self.build_path, context, buildEnv=self.buildEnv)
