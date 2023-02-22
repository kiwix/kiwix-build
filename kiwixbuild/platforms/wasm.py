from .base import PlatformInfo

from kiwixbuild.utils import pj
from kiwixbuild._global import get_target_step


class WasmPlatformInfo(PlatformInfo):
    name = 'wasm'
    static = True
    build = 'wasm'
    arch_full = 'wasm64-emscripten'
    libdir = "lib"
    #arch_full = 'wasm64-linux'
    toolchain_names = ['emsdk']
    compatible_hosts = ['fedora', 'debian']
    exe_wrapper_def = ""

    def get_cross_config(self):
        return {
            'binaries': self.binaries,
            'exe_wrapper_def': '',
            'root_path': self.root_path,
            'extra_libs': [],
            'extra_cflags': [],
            'host_machine': {
                'system': 'emscripten',
                'lsystem': 'emscripten',
                'cpu_family': 'wasm64',
                'cpu': 'wasm64',
                'endian': 'little',
                'abi': ''
            }
        }

    @property
    def wasm_sdk(self):
        return get_target_step('emsdk', self.name)

    @property
    def install_path(self):
        return self.wasm_sdk.install_path

    @property
    def root_path(self):
        return self.install_path

    @property
    def binaries(self):
        binaries = (('CC', 'emcc'),
                    ('CXX', 'em++'),
                    ('AR', 'emar'),
                    ('STRIP', 'emstrip'),
                    ('WINDRES', 'windres'),
                    ('RANLIB', 'emranlib'),
                    ('LD', 'wasm-ld'))
        binaries = {k:pj(self.install_path, 'upstream', 'emscripten', v)
                    for k,v in binaries}
        binaries['PKGCONFIG'] = 'pkg-config'
        return binaries

    @property
    def configure_option(self):
        #return ""
        return '--host={}'.format(self.arch_full)

    @property
    def configure_wrapper(self):
        return "emconfigure"

    @property
    def make_wrapper(self):
        return "emmake"

    def get_bin_dir(self):
        return [pj(self.install_path, 'bin')]

    def get_env(self):
        env = super().get_env()
        env['PATH'] = ':'.join([
            env['PATH'],
            self.install_path,
            pj(self.install_path, 'upstream', 'emscripten'),
            pj(self.install_path, 'node', '14.18.2_64bit', 'bin')
        ])
        env['EMSDK'] = self.install_path
        env['EMSDK_NODE'] = pj(self.install_path, 'node', '14.18.2_64bit', 'bin', 'node')
        return env

    def set_comp_flags(self, env):
        super().set_comp_flags(env)
        env['CFLAGS'] = " -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CFLAGS']
        env['CXXFLAGS'] = " -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4 "+env['CXXFLAGS']

    def set_compiler(self, env):
        for k, v in self.binaries.items():
            env[k] = v

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')
