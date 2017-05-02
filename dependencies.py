import shutil,os

from dependency_utils import (
    Dependency,
    ReleaseDownload,
    GitClone,
    MakeBuilder,
    CMakeBuilder,
    MesonBuilder,
    GradleBuilder,
    Builder as BaseBuilder)

from utils import Remotefile, pj, SkipCommand, copy_tree, add_execution_right

# *************************************
# Missing dependencies
# Is this ok to assume that those libs
# exist in your "distri" (linux/mac) ?
# If not, we need to compile them here
# *************************************
# aria2
# Argtable
# MSVirtual
# Android
# libiconv
# gettext
# *************************************


class zlib(Dependency):
    name = 'zlib'
    version = '1.2.8'

    class Source(ReleaseDownload):
        archive = Remotefile('zlib-1.2.8.tar.gz',
                             '36658cb768a54c1d4dec43c3116c27ed893e88b02ecfcb44f2166f9c0b7f2a0d')
        patches = ['zlib_std_libname.patch']

    class Builder(MakeBuilder):
        dynamic_configure_option = "--shared"
        static_configure_option = "--static"

        def _pre_build_script(self, context):
            context.try_skip(self.build_path)
            shutil.copytree(self.source_path, self.build_path)

        @property
        def all_configure_option(self):
            return '--static' if self.buildEnv.platform_info.static else '--shared'

        @property
        def configure_option(self):
            options = "-DINSTALL_PKGCONFIG_DIR={}".format(pj(self.buildEnv.install_dir, self.buildEnv.libprefix, 'pkgconfig'))
            if self.buildEnv.platform_info.static:
                options += " -DBUILD_SHARED_LIBS=false"
            else:
                options += " -DBUILD_SHARED_LIBS=true"
            return options

        def _configure(self, context):
            if self.buildEnv.platform_info.build == 'win32':
                raise SkipCommand()
            return super()._configure(context)

        @property
        def make_option(self):
            if self.buildEnv.platform_info.build == 'win32':
                return "--makefile win32/Makefile.gcc PREFIX={host}- SHARED_MODE={static} INCLUDE_PATH={include_path} LIBRARY_PATH={library_path} BINARY_PATH={binary_path}".format(
                    host='i686-w64-mingw32',
                    static="0" if self.buildEnv.platform_info.static else "1",
                    include_path=pj(self.buildEnv.install_dir, 'include'),
                    library_path=pj(self.buildEnv.install_dir, self.buildEnv.libprefix),
                    binary_path=pj(self.buildEnv.install_dir, 'bin'),
                    )
            return ""

class lzma(Dependency):
    name = 'lzma'
    version = '5.0.4'

    class Source(ReleaseDownload):
        archive = Remotefile('xz-5.0.4.tar.bz2',
                             '5cd9b060d3a1ad396b3be52c9b9311046a1c369e6062aea752658c435629ce92')

    class Builder(MakeBuilder):
        @property
        def configure_option(self):
            return "--disable-assembler"

class UUID(Dependency):
    name = 'uuid'
    version = "1.43.4"

    class Source(ReleaseDownload):
        archive = Remotefile('e2fsprogs-libs-1.43.4.tar.gz',
                             'eed4516325768255c9745e7b82c9d7d0393abce302520a5b2cde693204b0e419',
                             'https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v1.43.4/e2fsprogs-libs-1.43.4.tar.gz')
        extract_dir = 'e2fsprogs-libs-1.43.4'

    class Builder(MakeBuilder):
        configure_option = ("--enable-libuuid --disable-debugfs --disable-imager --disable-resizer --disable-defrag --enable-fsck"
                            " --disable-uuidd")
        configure_env = {'_format_CFLAGS': "{env.CFLAGS} -fPIC"}
        static_configure_option = dynamic_configure_option = ""
        make_target = 'libs'
        make_install_target = 'install-libs'


class Xapian(Dependency):
    name = "xapian-core"
    version = "1.4.2"

    class Source(ReleaseDownload):
        archive = Remotefile('xapian-core-1.4.2.tar.xz',
                             'aec2c4352998127a2f2316218bf70f48cef0a466a87af3939f5f547c5246e1ce')
        patches = ["xapian_pkgconfig.patch"]

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-inmemory --disable-documentation"
        configure_env = {'_format_LDFLAGS': "-L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS': "-I{buildEnv.install_dir}/include"}

    @property
    def dependencies(self):
        deps = ['zlib', 'lzma']
        if self.buildEnv.platform_info.build == 'win32':
            return deps
        return deps + ['uuid']


class CTPP2(Dependency):
    name = "ctpp2"
    version = "2.8.3"

    class Source(ReleaseDownload):
        archive = Remotefile('ctpp2-2.8.3.tar.gz',
                             'a83ffd07817adb575295ef40fbf759892512e5a63059c520f9062d9ab8fb42fc')
        patches = ["ctpp2_include.patch",
                   "ctpp2_no_src_modification.patch",
                   "ctpp2_fix-static-libname.patch",
                   "ctpp2_mingw32.patch",
                   "ctpp2_dll_export_VMExecutable.patch",
                   "ctpp2_win_install_lib_in_lib_dir.patch",
                   "ctpp2_iconv_support.patch"]

    class Builder(CMakeBuilder):
        configure_option = "-DMD5_SUPPORT=OFF"


class Pugixml(Dependency):
    name = "pugixml"
    version = "1.2"

    class Source(ReleaseDownload):
        archive = Remotefile('pugixml-1.2.tar.gz',
                             '0f422dad86da0a2e56a37fb2a88376aae6e931f22cc8b956978460c9db06136b')
        patches = ["pugixml_meson.patch"]

    Builder = MesonBuilder


class MicroHttpd(Dependency):
    name = "libmicrohttpd"
    version = "0.9.46"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.46.tar.gz',
                             '06dbd2654f390fa1e8196fe063fc1449a6c2ed65a38199a49bf29ad8a93b8979',
                             'http://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.46.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl"


class Icu(Dependency):
    name = "icu4c"
    version = "58_2"

    class Source(ReleaseDownload):
        name = "icu4c"

        @property
        def source_dir(self):
            return "{}-{}".format(self.name, self.target.version)

        archive = Remotefile('icu4c-58_2-src.tgz',
                             '2b0a4410153a9b20de0e20c7d8b66049a72aef244b53683d0d7521371683da0c',
                             'https://freefr.dl.sourceforge.net/project/icu/ICU4C/58.2/icu4c-58_2-src.tgz')
        patches = ["icu4c_fix_static_lib_name_mingw.patch",
                   "icu4c_android_elf64_st_info.patch"]
        data = Remotefile('icudt56l.dat',
                          'e23d85eee008f335fc49e8ef37b1bc2b222db105476111e3d16f0007d371cbca')

        def _download_data(self, context):
            self.buildEnv.download(self.data)

        def _copy_data(self, context):
            context.try_skip(self.extract_path)
            shutil.copyfile(pj(self.buildEnv.archive_dir, self.data.name), pj(self.extract_path, 'source', 'data', 'in', self.data.name))

        def prepare(self):
            super().prepare()
            self.command("download_data", self._download_data)
            self.command("copy_data", self._copy_data)

    class Builder(MakeBuilder):
        subsource_dir = "source"
        configure_option = "--disable-samples --disable-tests --disable-extras --disable-dyload"


class Icu_native(Icu):
    name = "icu4c_native"
    force_native_build = True

    class Builder(Icu.Builder):
        @property
        def build_path(self):
            return super().build_path+"_native"

        def _install(self, context):
            raise SkipCommand()


class Icu_cross_compile(Icu):
    name = "icu4c_cross-compile"
    dependencies = ['icu4c_native']

    class Builder(Icu.Builder):
        @property
        def configure_option(self):
            icu_native_dep = self.buildEnv.targetsDict['icu4c_native']
            return super().configure_option + " --with-cross-build=" + icu_native_dep.builder.build_path


class Libzim(Dependency):
    name = "libzim"

    @property
    def dependencies(self):
        base_dependencies = ['zlib', 'lzma', 'xapian-core']
        if self.buildEnv.platform_info.build != 'native':
            return base_dependencies + ["icu4c_cross-compile"]
        else:
            return base_dependencies + ["icu4c"]

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    Builder = MesonBuilder


class Zimwriterfs(Dependency):
    name = "zimwriterfs"
    extra_packages = ['file', 'gumbo']

    @property
    def dependencies(self):
        base_dependencies = ['libzim', 'zlib', 'lzma', 'xapian-core']
        if self.buildEnv.platform_info.build != 'native':
            return base_dependencies + ["icu4c_cross-compile"]
        else:
            return base_dependencies + ["icu4c"]

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zimwriterfs.git"
        git_dir = "zimwriterfs"

        def _post_prepare_script(self, context):
            context.try_skip(self.git_path)
            command = "./autogen.sh"
            self.buildEnv.run_command(command, self.git_path, context)

    Builder = MakeBuilder


class Kiwixlib(Dependency):
    name = "kiwix-lib"

    @property
    def dependencies(self):
        base_dependencies = ["pugixml", "libzim", "zlib", "lzma"]
        if self.buildEnv.platform_info.build != 'android':
            base_dependencies += ['ctpp2']
        if self.buildEnv.platform_info.build != 'native':
            return base_dependencies + ["icu4c_cross-compile"]
        else:
            return base_dependencies + ["icu4c"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-lib.git"
        git_dir = "kiwix-lib"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
            base_option = "-Dctpp2-install-prefix={buildEnv.install_dir}"
            if self.buildEnv.platform_info.build == 'android':
                base_option += ' -Dandroid=true'
            return base_option

        @property
        def library_type(self):
            if self.buildEnv.platform_info.build == 'android':
                return 'shared'
            return super().library_type


class KiwixTools(Dependency):
    name = "kiwix-tools"
    dependencies = ["kiwix-lib", "libmicrohttpd", "zlib"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-tools.git"
        git_dir = "kiwix-tools"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
            if self.buildEnv.platform_info.static:
                return "-Dstatic-linkage=true"
            return ""


class Gradle(Dependency):
    name = "Gradle"
    version = "3.4"

    class Source(ReleaseDownload):
        archive = Remotefile('gradle-3.4-bin.zip',
                             '72d0cd4dcdd5e3be165eb7cd7bbd25cf8968baf400323d9ab1bba622c3f72205',
                             'https://services.gradle.org/distributions/gradle-3.4-bin.zip')

    class Builder(BaseBuilder):
        def build(self):
            self.command('install', self._install)

        def _install(self, context):
            copy_tree(
                pj(self.source_path, "bin"),
                pj(self.buildEnv.install_dir, "bin"),
                post_copy_function = add_execution_right)
            copy_tree(
                pj(self.source_path, "lib"),
                pj(self.buildEnv.install_dir, "lib"))


class KiwixAndroid(Dependency):
    name = "kiwix-android"
    dependencies = ["Gradle", "kiwix-lib"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-android"
        git_dir = "kiwix-android"

    class Builder(GradleBuilder):
        def _configure(self, context):
            if not os.path.exists(self.build_path):
                shutil.copytree(self.source_path, self.build_path)
            try:
                shutil.rmtree(pj(self.build_path, 'kiwixlib', 'src', 'main'))
            except FileNotFoundError:
                pass
            shutil.copytree(pj(self.buildEnv.install_dir, 'kiwix-lib'), pj(self.build_path, 'kiwixlib', 'src', 'main'))
