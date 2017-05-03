import os.path
import hashlib
import tarfile, zipfile
import tempfile
import shutil
import os, stat
from collections import namedtuple, defaultdict

pj = os.path.join


class Defaultdict(defaultdict):
    def __getattr__(self, name):
        return self[name]


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


def get_sha256(path):
    progress_chars = "/-\|"
    current = 0
    batch_size = 1024 * 8
    sha256 = hashlib.sha256()
    with open(path, 'br') as f:
        while True:
            batch = f.read(batch_size)
            if not batch:
                break
            sha256.update(batch)
            print_status(progress_chars[current])
            current = (current+1)%4
    return sha256.hexdigest()

def print_status(status):
    text = "{}\033[{}D".format(status, len(status))
    print(text, end="")

def add_execution_right(file_path):
    current_permissions = stat.S_IMODE(os.lstat(file_path).st_mode)
    os.chmod(file_path, current_permissions | stat.S_IXUSR)

def copy_tree(src, dst, post_copy_function=None):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        r = os.path.relpath(root, src)
        dstdir = pj(dst, r)
        os.makedirs(dstdir, exist_ok=True)
        for f in files:
            dstfile = pj(dstdir, f)
            shutil.copy2(pj(root, f), dstfile)
            if post_copy_function is not None:
                post_copy_function(dstfile)

class SkipCommand(Exception):
    pass


class StopBuild(Exception):
    pass


class Remotefile(namedtuple('Remotefile', ('name', 'sha256', 'url'))):
    def __new__(cls, name, sha256, url=None):
        return super().__new__(cls, name, sha256, url)


class Context:
    def __init__(self, command_name, log_file, force_native_build):
        self.command_name = command_name
        self.log_file = log_file
        self.force_native_build = force_native_build
        self.autoskip_file = None

    def try_skip(self, path):
        self.autoskip_file = pj(path, ".{}_ok".format(self.command_name))
        if os.path.exists(self.autoskip_file):
            raise SkipCommand()

    def _finalise(self):
        if self.autoskip_file is not None:
            with open(self.autoskip_file, 'w'):
                pass


def extract_archive(archive_path, dest_dir, topdir=None, name=None):
    is_zip_archive = archive_path.endswith('.zip')
    try:
        if is_zip_archive:
            archive = zipfile.ZipFile(archive_path)
            members = archive.infolist()
            getname = lambda info : info.filename
            isdir = lambda info: info.filename.endswith('/')
        else:
            archive = tarfile.open(archive_path)
            members = archive.getmembers()
            getname = lambda info : getattr(info, 'name')
            isdir = lambda info: info.isdir()
        if not topdir:
            for d in (m for m in members if isdir(m)):
                _name = getname(d)
                if _name.endswith('/'):
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
            members_to_extract = [m for m in members if getname(m).startswith(topdir+'/')]
            os.makedirs(dest_dir, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=os.path.basename(archive_path), dir=dest_dir) as tmpdir:
                if is_zip_archive:
                    _members_to_extract = [getname(m) for m in members_to_extract]
                else:
                    _members_to_extract = members_to_extract
                archive.extractall(path=tmpdir, members=_members_to_extract)
                if is_zip_archive:
                    for member in members_to_extract:
                        if isdir(member):
                            continue
                        perm = (member.external_attr >> 16) & 0x1FF
                        os.chmod(pj(tmpdir, getname(member)), perm)
                name = name or topdir
                os.rename(pj(tmpdir, topdir), pj(dest_dir, name))
        else:
            if name:
                dest_dir = pj(dest_dir, name)
                os.makedirs(dest_dir)
            archive.extractall(path=dest_dir)
    finally:
        if archive is not None:
            archive.close()

