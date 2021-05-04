from .base import (
    Dependency,
    GitClone,
    MesonBuilder)
from kiwixbuild._global import option, get_target_step

class Libzim(Dependency):
    name = "libzim"
    force_build = True

    class Source(GitClone):
        git_remote = "https://github.com/openzim/libzim.git"
        git_dir = "libzim"

    class Builder(MesonBuilder):
        test_option = "-t 8"
        dependencies = ['lzma', 'zstd', 'xapian-core', 'icu4c', 'zim-testing-suite']
        strip_option = ''

        @property
        def configure_option(self):
            platformInfo = self.buildEnv.platformInfo
            zim_testing_suite = get_target_step('zim-testing-suite', platformInfo.name)
            config_options = ['-Dtest_data_dir={}'.format(zim_testing_suite.source_path)]
            if platformInfo.build == 'android':
                config_options.append("-DUSE_BUFFER_HEADER=false")
            if platformInfo.build == 'iOS':
                config_options.append("-Db_bitcode=true")
            if platformInfo.name == 'native_mixed' and option('target') == 'libzim':
                config_options.append("-Dstatic-linkage=true")
            if platformInfo.name == "flatpak":
                config_options.append("--wrap-mode=nodownload")
            return " ".join(config_options)
