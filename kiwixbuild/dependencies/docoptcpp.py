from .base import Dependency, GitClone, CMakeBuilder

from kiwixbuild.utils import Remotefile


class docoptcpp(Dependency):
    name = "docoptcpp"

    class Source(GitClone):
        git_remote = "https://github.com/docopt/docopt.cpp.git"
        git_dir = "docopt.cpp"
        force_full_clone = True
        git_ref = "3dd23e3280f213bacefdf5fcb04857bf52e90917"

    class Builder(CMakeBuilder):
        make_install_targets = ["install"]
