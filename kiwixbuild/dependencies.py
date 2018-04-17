import shutil, os, json
from urllib.parse import urlparse

from kiwixbuild.dependency_utils import (
    Dependency,
    ReleaseDownload,
    GitClone,
    SvnClone,
    NoopSource,
    MakeBuilder,
    CMakeBuilder,
    MesonBuilder,
    GradleBuilder,
    NoopBuilder,
    Builder as BaseBuilder)

from kiwixbuild.utils import Remotefile, pj, SkipCommand, copy_tree, add_execution_right

# *************************************
# Missing dependencies
# Is this ok to assume that those libs
# exist in your "distri" (linux/mac) ?
# If not, we need to compile them here
# *************************************
# Argtable
# MSVirtual
# Android
# libiconv
# gettext
# *************************************


class zlib(Dependency):
    name = 'zlib'

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

    class Source(ReleaseDownload):
        archive = Remotefile('xz-5.2.3.tar.bz2',
                             'fd9ca16de1052aac899ad3495ad20dfa906c27b4a5070102a2ec35ca3a4740c1',
                             'https://tukaani.org/xz/xz-5.2.3.tar.bz2')

    class Builder(MakeBuilder):
        @property
        def configure_option(self):
            return "--disable-assembler --disable-xz --disable-xzdec"

class UUID(Dependency):
    name = 'uuid'

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

    class Source(ReleaseDownload):
        archive = Remotefile('xapian-core-1.4.5.tar.xz',
                             '85b5f952de9df925fd13e00f6e82484162fd506d38745613a50b0a2064c6b02b')

    class Builder(MakeBuilder):
        configure_option = "--disable-sse --disable-backend-inmemory --disable-documentation"
        configure_env = {'_format_LDFLAGS': "-L{buildEnv.install_dir}/{buildEnv.libprefix}",
                         '_format_CXXFLAGS': "-I{buildEnv.install_dir}/include"}

    @property
    def dependencies(self):
        deps = ['zlib', 'lzma']
        if (self.buildEnv.platform_info.build == 'win32'
         or self.buildEnv.distname == 'Darwin'):
            return deps
        return deps + ['uuid']


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
        configure_option = "-DMD5_SUPPORT=OFF -DICONV_SUPPORT=OFF"


class CTPP2C(CTPP2):
    name = "ctpp2c"
    force_native_build = True

    class Builder(CTPP2.Builder):
        make_target = "ctpp2c"

        @property
        def build_path(self):
            return super().build_path+"_native"

        def _install(self, context):
            context.try_skip(self.build_path)
            command = "cp {ctpp2c}* {install_dir}".format(
                ctpp2c=pj(self.build_path, 'ctpp2c'),
                install_dir=pj(self.buildEnv.install_dir, 'bin')
            )
            self.buildEnv.run_command(command, self.build_path, context)


class Pugixml(Dependency):
    name = "pugixml"

    class Source(ReleaseDownload):
        archive = Remotefile('pugixml-1.2.tar.gz',
                             '0f422dad86da0a2e56a37fb2a88376aae6e931f22cc8b956978460c9db06136b')
        patches = ["pugixml_meson.patch"]

    Builder = MesonBuilder


class MicroHttpd(Dependency):
    name = "libmicrohttpd"

    class Source(ReleaseDownload):
        archive = Remotefile('libmicrohttpd-0.9.46.tar.gz',
                             '06dbd2654f390fa1e8196fe063fc1449a6c2ed65a38199a49bf29ad8a93b8979',
                             'http://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.46.tar.gz')

    class Builder(MakeBuilder):
        configure_option = "--disable-https --without-libgcrypt --without-libcurl"


class Aria2(Dependency):
    name = "libaria2"
    dependencies = ['zlib']

    class Source(ReleaseDownload):
        archive = Remotefile('libaria2-1.33.1.tar.gz',
                             '0616f11ef3ddd0c74be74ea2536be62ce168b99e3d6a35dea9d166b9cab9fbd1',
                             'https://github.com/aria2/aria2/archive/release-1.33.1.tar.gz')

        patches = ["libaria2_android.patch"]

        def _post_prepare_script(self, context):
            context.try_skip(self.extract_path)
            command = "autoreconf -i"
            self.buildEnv.run_command(command, self.extract_path, context)

    class Builder(MakeBuilder):
        configure_option = "--enable-libaria2 --disable-ssl --disable-bittorent --disable-metalink"


class Gumbo(Dependency):
    name = "gumbo"

    class Source(ReleaseDownload):
        archive = Remotefile('gumbo-0.10.1.tar.gz',
                             '28463053d44a5dfbc4b77bcf49c8cee119338ffa636cc17fc3378421d714efad',
                             'https://github.com/google/gumbo-parser/archive/v0.10.1.tar.gz')

        def _post_prepare_script(self, context):
            context.try_skip(self.extract_path)
            command = "./autogen.sh"
            self.buildEnv.run_command(command, self.extract_path, context)

    Builder = MakeBuilder


class Icu(Dependency):
    name = "icu4c"

    class Source(SvnClone):
        name = "icu4c"
        svn_remote = "http://source.icu-project.org/repos/icu/tags/release-58-2/icu4c"
        svn_dir = "icu4c"

        patches = ["icu4c_fix_static_lib_name_mingw.patch",
                   "icu4c_android_elf64_st_info.patch",
                   "icu4c_custom_data.patch",
                   "icu4c_noxlocale.patch",
                   "icu4c_rpath.patch"]


    class Builder(MakeBuilder):
        subsource_dir = "source"

        @property
        def configure_option(self):
            options = "--disable-samples --disable-tests --disable-extras --disable-dyload --enable-rpath"
            if self.buildEnv.platform_info.build == 'android':
                options += " --with-data-packaging=archive"
            return options


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
            return super().configure_option + " --with-cross-build={} --disable-tools".format(icu_native_dep.builder.build_path)


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

    class Builder(MesonBuilder):
        test_option = "-t 8"


class ZimTools(Dependency):
    name = "zim-tools"
    dependencies = ['libzim']

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zim-tools.git"
        git_dir = "zim-tools"

    class Builder(MesonBuilder):
        @property
        def configure_option(self):
            if self.buildEnv.platform_info.static:
                return "-Dstatic-linkage=true"
            return ""


class Zimwriterfs(Dependency):
    name = "zimwriterfs"
    extra_packages = ['file']

    @property
    def dependencies(self):
        base_dependencies = ['libzim', 'zlib', 'lzma', 'xapian-core', 'gumbo']
        if self.buildEnv.platform_info.build != 'native':
            return base_dependencies + ["icu4c_cross-compile"]
        else:
            return base_dependencies + ["icu4c"]

    class Source(GitClone):
        git_remote = "https://github.com/openzim/zimwriterfs.git"
        git_dir = "zimwriterfs"
        release_git_ref = "1.1"

        def _post_prepare_script(self, context):
            context.try_skip(self.git_path)
            command = "./autogen.sh"
            self.buildEnv.run_command(command, self.git_path, context)

    Builder = MakeBuilder


class Kiwixlib(Dependency):
    name = "kiwix-lib"

    @property
    def dependencies(self):
        base_dependencies = ["pugixml", "libzim", "zlib", "lzma", "libaria2"]
        if ( self.buildEnv.platform_info.build != 'android'
          and self.buildEnv.distname != 'Darwin'):
            base_dependencies += ['ctpp2c', 'ctpp2']
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

    class Source(ReleaseDownload):
        archive = Remotefile('gradle-4.6-bin.zip',
                             '98bd5fd2b30e070517e03c51cbb32beee3e2ee1a84003a5a5d748996d4b1b915',
                             'https://services.gradle.org/distributions/gradle-4.6-bin.zip')

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


class AllBaseDependencies(Dependency):
    name = "alldependencies"

    @property
    def dependencies(self):
        base_deps = ['zlib', 'lzma', 'xapian-core', 'gumbo', 'pugixml', 'libmicrohttpd', 'libaria2']
        if self.buildEnv.platform_info.build != 'native':
            base_deps += ["icu4c_cross-compile"]
        else:
            base_deps += ["icu4c"]
        if ( self.buildEnv.platform_info.build != 'android'
           and self.buildEnv.distname != 'Darwin'):
            base_deps += ['ctpp2c', 'ctpp2']
        if self.buildEnv.platform_info.build == 'android':
            base_deps += ['Gradle']

        return base_deps


    Source = NoopSource
    Builder = NoopBuilder


class KiwixAndroid(Dependency):
    name = "kiwix-android"
    dependencies = ["Gradle", "kiwix-lib"]

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-android"
        git_dir = "kiwix-android"

    class Builder(GradleBuilder):
        def build(self):
            if self.buildEnv.options.targets == 'kiwix-android-custom':
                print("SKIP")
            else:
                super().build()

        def _configure(self, context):
            if not os.path.exists(self.build_path):
                shutil.copytree(self.source_path, self.build_path, symlinks=True)
            try:
                shutil.rmtree(pj(self.build_path, 'kiwixlib', 'src', 'main'))
            except FileNotFoundError:
                pass
            shutil.copytree(pj(self.buildEnv.install_dir, 'kiwix-lib'),
                            pj(self.build_path, 'kiwixlib', 'src', 'main'))
            os.makedirs(
                pj(self.build_path, 'app', 'src', 'main', 'assets', 'icu'),
                exist_ok=True)
            shutil.copy2(pj(self.buildEnv.install_dir, 'share', 'icu', '58.2',
                            'icudt58l.dat'),
                         pj(self.build_path, 'app', 'src', 'main', 'assets',
                            'icu', 'icudt58l.dat'))


class KiwixCustomApp(Dependency):
    name = "kiwix-android-custom"
    dependencies = ["kiwix-android", "kiwix-lib"]

    def __init__(self, buildEnv):
        super().__init__(buildEnv)
        self.custom_name = buildEnv.options.android_custom_app

    class Source(GitClone):
        git_remote = "https://github.com/kiwix/kiwix-android-custom"
        git_dir = "kiwix-android-custom"

    class Builder(GradleBuilder):
        @property
        def gradle_target(self):
            return "assemble{}".format(self.target.custom_name)

        @property
        def gradle_option(self):
            template = ("-i -P customDir={customDir}"
                        " -P zim_file_size={zim_size}"
                        " -P version_code={version_code}"
                        " -P version_name={version_name}"
                        " -P content_version_code={content_version_code}")
            return template.format(
                customDir=pj(self.build_path, 'custom'),
                zim_size=self._get_zim_size(),
                version_code=os.environ['VERSION_CODE'],
                version_name=os.environ['VERSION_NAME'],
                content_version_code=os.environ['CONTENT_VERSION_CODE'])

        @property
        def build_path(self):
            return pj(self.buildEnv.build_dir, "{}_{}".format(self.target.full_name, self.target.custom_name))

        @property
        def custom_build_path(self):
            return pj(self.build_path, 'custom', self.target.custom_name)

        def _get_zim_size(self):
            try:
                zim_size = self.buildEnv.options.zim_file_size
            except AttributeError:
                with open(pj(self.source_path, self.target.custom_name, 'info.json')) as f:
                    app_info = json.load(f)
                zim_size = os.path.getsize(pj(self.custom_build_path, app_info['zim_file']))
            return zim_size

        def build(self):
            self.command('configure', self._configure)
            self.command('download_zim', self._download_zim)
            self.command('compile', self._compile)

        def _download_zim(self, context):
            zim_url = self.buildEnv.options.zim_file_url
            if zim_url is None:
                raise SkipCommand()
            with open(pj(self.source_path, self.target.custom_name, 'info.json')) as f:
                app_info = json.load(f)
            zim_url = app_info.get('zim_url', zim_url)
            out_filename = urlparse(zim_url).path
            out_filename = os.path.basename(out_filename)
            zim_file = Remotefile(out_filename, '', zim_url)
            self.buildEnv.download(zim_file)
            shutil.copy(pj(self.buildEnv.archive_dir, out_filename),
                        pj(self.custom_build_path, app_info['zim_file']))

        def _configure(self, context):
            # Copy kiwix-android in build dir.
            kiwix_android_dep = self.buildEnv.targetsDict['kiwix-android']
            if not os.path.exists(self.build_path):
                shutil.copytree(kiwix_android_dep.source_path, self.build_path)

            # Copy kiwix-lib application in build dir
            try:
                shutil.rmtree(pj(self.build_path, 'kiwixlib', 'src', 'main'))
            except FileNotFoundError:
                pass
            shutil.copytree(pj(self.buildEnv.install_dir, 'kiwix-lib'),
                            pj(self.build_path, 'kiwixlib', 'src', 'main'))
            os.makedirs(
                pj(self.build_path, 'app', 'src', 'main', 'assets', 'icu'),
                exist_ok=True)
            shutil.copy2(pj(self.buildEnv.install_dir, 'share', 'icu', '58.2',
                            'icudt58l.dat'),
                         pj(self.build_path, 'app', 'src', 'main', 'assets',
                            'icu', 'icudt58l.dat'))

            # Generate custom directory
            try:
                shutil.rmtree(pj(self.build_path, 'custom'))
            except FileNotFoundError:
                pass
            os.makedirs(pj(self.build_path, 'custom'))
            command = "./gen-custom-android-directory.py {custom_name} --output-dir {custom_dir}"
            command = command.format(
                custom_name=self.target.custom_name,
                custom_dir=pj(self.build_path, 'custom', self.target.custom_name)
            )
            self.buildEnv.run_command(command, self.source_path, context)
