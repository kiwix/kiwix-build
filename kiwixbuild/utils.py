import hashlib
import tarfile, zipfile
import tempfile
import shutil
import os, stat, sys
import urllib.request
import urllib.error
import ssl
import subprocess
import re
from pathlib import Path, PurePosixPath
from collections import namedtuple, defaultdict

from kiwixbuild._global import neutralEnv, option


COLORS = {
    "OK": "\033[92m",
    "WARNING": "\033[93m",
    "NEEDED": "\033[93m",
    "SKIP": "\033[34m",
    "ERROR": "\033[91m",
    "": "\033[0m",
}


REMOTE_PREFIX = "http://mirror.download.kiwix.org/dev/kiwix-build/"


def which(name):
    command = f"which {name}"
    output = subprocess.check_output(command, shell=True)
    return output[:-1].decode()


def xrun_find(name):
    command = f"xcrun -find {name}"
    output = subprocess.check_output(command, shell=True)
    return output[:-1].decode()


def enclose(part: str) -> str:
    if " " in part:
        return f"'{part}'"
    return part


def escape_path(path: Path):
    path = Path(path)
    parts = [enclose(p) for p in path.parts]
    path = Path(*parts)
    return str(path)


class Defaultdict(defaultdict):
    def __getattr__(self, name):
        return self[name]


class DefaultEnv(Defaultdict):
    def __init__(self):
        super().__init__(str, os.environ)

    def __getitem__(self, name):
        if name == b"PATH":
            raise KeyError
        if name in ["PATH", "PKG_CONFIG_PATH", "LD_LIBRARY_PATH"]:
            item = super().__getitem__(name)
            if isinstance(item, PathArray):
                return item
            else:
                item = PathArray(item)
                self[name] = item
                return item
        return super().__getitem__(name)


def get_separator():
    return ";" if neutralEnv("distname") == "Windows" else ":"


class PathArray(list):
    def __init__(self, value):
        self.separator = get_separator()
        if not value:
            super().__init__([])
        else:
            super().__init__(value.split(self.separator))

    def __str__(self):
        return self.separator.join((escape_path(v) for v in self))


def remove_duplicates(iterable, key_function=None):
    seen = set()
    if key_function is None:
        key_function = lambda e: e
    for elem in iterable:
        key = key_function(elem)
        if key in seen:
            continue
        seen.add(key)
        yield elem


def get_sha256(path: Path):
    progress_chars = "/-\\|"
    current = 0
    batch_size = 1024 * 8
    sha256 = hashlib.sha256()
    with path.open("br") as f:
        while True:
            batch = f.read(batch_size)
            if not batch:
                break
            sha256.update(batch)
            print_progress(progress_chars[current])
            current = (current + 1) % 4
    return sha256.hexdigest()


def colorize(text, color=None):
    if color is None:
        color = text
    return f"{COLORS[color]}{text}{COLORS['']}"


def print_progress(progress):
    if option("show_progress"):
        text = f"{progress}\033[{len(progress)}D"
        print(text, end="")


def add_execution_right(file_path: Path):
    current_permissions = stat.S_IMODE(os.lstat(file_path).st_mode)
    file_path.chmod(current_permissions | stat.S_IXUSR)


def copy_tree(src: Path, dst: Path, post_copy_function=None):
    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in src.walk():
        r = root.relative_to(src)
        dstdir = dst / r
        dstdir.mkdir(exist_ok=True)
        for f in files:
            dstfile = dstdir / f
            shutil.copy2(root / f, dstfile, follow_symlinks=False)
            if post_copy_function is not None:
                post_copy_function(dstfile)


class Remotefile(namedtuple("Remotefile", ("name", "sha256", "url"))):
    def __new__(cls, name, sha256, url=None):
        if url is None:
            url = REMOTE_PREFIX + name
        return super().__new__(cls, name, sha256, url)


def download_remote(what: Remotefile, where: Path):
    file_path = where / what.name
    if file_path.exists():
        if what.sha256 == get_sha256(file_path):
            raise SkipCommand()
        file_path.unlink()

    if option("no_cert_check"):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context = None
    batch_size = 1024 * 8
    extra_args = {"context": context} if sys.version_info >= (3, 4, 3) else {}
    progress_chars = "/-\\|"
    try:
        with urllib.request.urlopen(what.url, **extra_args) as resource, file_path.open(
            "wb"
        ) as file:
            tsize = resource.info().get("Content-Length", None)
            if tsize is not None:
                tsize = int(tsize)
            current = 0
            while True:
                batch = resource.read(batch_size)
                if not batch:
                    break
                if tsize:
                    current += batch_size
                    print_progress(f"{current/tsize:.2%}")
                else:
                    print_progress(progress_chars[current])
                    current = (current + 1) % 4
                file.write(batch)
    except urllib.error.URLError as e:
        print(f"Cannot download url {what.url}:\n{e.reason}")
        raise StopBuild()

    if not what.sha256:
        print(f"Sha256 for {what.name} not set, do no verify download")
    elif what.sha256 != get_sha256(file_path):
        file_path.unlink()
        raise StopBuild("Sha 256 doesn't correspond")


class BaseCommandResult(Exception):
    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self):
        return self.msg


class SkipCommand(BaseCommandResult):
    def __str__(self):
        if self.msg:
            return colorize("SKIP") + f" : {self.msg}"
        return colorize("SKIP")


class WarningMessage(BaseCommandResult):
    def __str__(self):
        return colorize("WARNING") + f" : {self.msg}"


class StopBuild(BaseCommandResult):
    pass


class Context:
    def __init__(self, command_name, log_file, force_native_build):
        self.command_name = command_name
        self.log_file = log_file
        self.force_native_build = force_native_build
        self.autoskip_file = None
        self.no_skip = False

    def skip(self, msg=""):
        raise SkipCommand(msg)

    def try_skip(self, path: Path, extra_name=""):
        if self.no_skip:
            return
        if extra_name:
            extra_name = f"_{extra_name}"
        self.autoskip_file = path / f".{self.command_name}{extra_name}_ok"
        if self.autoskip_file.exists():
            raise SkipCommand()

    def _finalise(self):
        if self.autoskip_file is not None:
            self.autoskip_file.parent.mkdir(parents=True, exist_ok=True)
            self.autoskip_file.touch()


def extract_archive(archive_path: Path, dest_dir: Path, topdir=None, name=None):
    """Extract an archive to dest_dir.
    This archive can be a zip or a tar archive.
    If topdir is given, only this directory (and sub files/dirs) will be extracted.
    If name is given, the topdir will be extracted under this name.
    """
    is_zip_archive = archive_path.suffix == ".zip"
    archive = None
    try:
        if is_zip_archive:
            archive = zipfile.ZipFile(archive_path)
            members = archive.infolist()
            getname = lambda info: info.filename
            isdir = lambda info: info.filename.endswith("/")
        else:
            archive = tarfile.open(archive_path)
            members = archive.getmembers()
            getname = lambda info: getattr(info, "name")
            isdir = lambda info: info.isdir()
        if not topdir:
            for d in (m for m in members if isdir(m)):
                _name = getname(d)
                if _name.endswith("/"):
                    _name = _name[:-1]
                if not os.path.dirname(_name):
                    if topdir:
                        # There is already a top dir.
                        # Two topdirs in the same archive.
                        # Extract all
                        topdir = None
                        break
                    topdir = _name
        if topdir:
            members_to_extract = [
                m for m in members if getname(m).startswith(topdir + "/")
            ]
            dest_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix=archive_path.name, dir=dest_dir
            ) as tmpdir:
                tmpdir_path = Path(tmpdir)
                if is_zip_archive:
                    _members_to_extract = [getname(m) for m in members_to_extract]
                else:
                    _members_to_extract = members_to_extract
                archive.extractall(path=tmpdir_path, members=_members_to_extract)
                if is_zip_archive:
                    for member in members_to_extract:
                        if isdir(member):
                            continue
                        perm = (member.external_attr >> 16) & 0x1FF
                        if perm:
                            (tmpdir_path / getname(member)).chmod(perm)
                name = name or topdir
                shutil.copytree(
                    tmpdir_path / topdir,
                    dest_dir / name,
                    symlinks=True,
                    dirs_exist_ok=True,
                )
                # Be sure that all directory in tmpdir are writable to allow correct suppersion of it
                for root, dirs, _files in tmpdir_path.walk():
                    for d in dirs:
                        (root / d).chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)

        else:
            if name:
                dest_dir = dest_dir / name
                dest_dir.mkdir(parents=True)
            archive.extractall(path=dest_dir)
    finally:
        if archive is not None:
            archive.close()


def win_to_posix_path(p: Path or str) -> str:
    if isinstance(p, Path):
        return str(PurePosixPath(p)).replace("C:/", "/c/")
    return p


def run_command(command, cwd, context, *, env=None, input=None, force_posix_path=False):
    os.makedirs(cwd, exist_ok=True)
    if env is None:
        env = DefaultEnv()
    log = None
    if force_posix_path:
        transform_path = win_to_posix_path
    else:
        transform_path = lambda v: v
    command = [str(transform_path(v)) for v in command]
    try:
        if not option("verbose"):
            log = open(context.log_file, "w")
        print(f"run command '{command}'", file=log)
        print(f"current directory is '{cwd}'", file=log)
        print("env is :", file=log)
        env = {k: str(transform_path(v)) for k, v in env.items()}
        for k, v in env.items():
            print(f"  {k} : {v!r}", file=log)

        if log:
            log.flush()
        kwargs = dict()
        if input:
            kwargs["stdin"] = subprocess.PIPE
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=log or sys.stdout,
            stderr=subprocess.STDOUT,
            **kwargs,
        )
        if input:
            input = input.encode()
        while True:
            try:
                if input is None:
                    process.wait(timeout=30)
                else:
                    process.communicate(input, timeout=30)
            except subprocess.TimeoutExpired:
                # Either `wait` timeout (and `input` is None) or
                # `communicate` timeout (and we must set `input` to None
                # to not communicate again).
                input = None
                print(".", end="", flush=True)
            else:
                break
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, command)
    finally:
        if log:
            log.close()
