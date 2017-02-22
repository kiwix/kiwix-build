import os.path
import hashlib
import tarfile
import tempfile
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
    sha256 = hashlib.sha256()
    with open(path, 'br') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


class SkipCommand(Exception):
    pass


class StopBuild(Exception):
    pass


class Remotefile(namedtuple('Remotefile', ('name', 'sha256', 'url'))):
    def __new__(cls, name, sha256, url=None):
        return super().__new__(cls, name, sha256, url)


class Context:
    def __init__(self, command_name, log_file):
        self.command_name = command_name
        self.log_file = log_file
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
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        if not topdir:
            for d in (m for m in members if m.isdir()):
                if not os.path.dirname(d.name):
                    if topdir:
                        # There is already a top dir.
                        # Two topdirs in the same archive.
                        # Extract all
                        topdir = None
                        break
                    topdir = d
        else:
            topdir = archive.getmember(topdir)
        if topdir:
            members_to_extract = [m for m in members if m.name.startswith(topdir.name+'/')]
            os.makedirs(dest_dir, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=os.path.basename(archive_path), dir=dest_dir) as tmpdir:
                archive.extractall(path=tmpdir, members=members_to_extract)
                name = name or topdir.name
                os.rename(pj(tmpdir, topdir.name), pj(dest_dir, name))
        else:
            if name:
                dest_dir = pj(dest_dir, name)
                os.makedirs(dest_dir)
            archive.extractall(path=dest_dir)
