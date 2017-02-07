#!/usr/bin/env python3

import os, sys, stat
import argparse
import datetime
import subprocess
import tarfile
import zipfile

pj = os.path.join

FILES_TO_UPLOAD = [
    'kiwix-index',
    'kiwix-install',
    'kiwix-manage',
    'kiwix-read',
    'kiwix-search',
    'kiwix-serve'
]

class Archiver:
    def __init__(self, options):
        self.options = options
        self.archive_basename = "kiwix-tools.{:%Y-%m-%d}".format(datetime.date.today())
        self.files_to_upload = list(self._gen_file_list())

    def _gen_file_list(self):
        bin_dir = pj(self.options.install_dir, 'bin')
        for filename in os.listdir(bin_dir):
            basename, _ = os.path.splitext(filename)
            if basename in FILES_TO_UPLOAD:
                yield pj(bin_dir, filename), pj(self.archive_basename, filename)

    def build_tar(self):
        archive_name = "{}.tar.gz".format(self.archive_basename)
        with tarfile.open(archive_name, "w:gz") as archive:
            for filename, arcname in self.files_to_upload:
                archive.add(filename, arcname=arcname)
        return archive_name

    def build_zip(self):
        archive_name = "{}.zip".format(self.archive_basename)
        with zipfile.ZipFile(archive_name, "w") as archive:
            for filename, arcname in self.files_to_upload:
                archive.write(filename, arcname)
        return archive_name


class Deployer:
    def __init__(self, options):
        self.options = options

    def deploy(self, *files):
        if not files:
            return
        command = "scp -v -p -i {id_file} {files_list} {host_addr}".format(
            id_file=self.options.ssh_private_key,
            files_list=' '.join("'{}'".format(f) for f in files),
            host_addr="{}:{}".format(self.options.server, self.options.base_path)
        )
        return subprocess.check_call(command, shell=True)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('install_dir')
    parser.add_argument('--deploy', action="store_true")
    group = parser.add_argument_group('deploy options')
    group.add_argument('--ssh_private_key')
    group.add_argument('--server')
    group.add_argument('--base_path')
    parser.add_argument('--tar', action="store_true")
    parser.add_argument('--zip', action="store_true")
    parser.add_argument('--verbose', '-v', action="store_true",
                        help=("Print all logs on stdout instead of in specific"
                              " log files per commands"))
    return parser.parse_args()

if __name__ == "__main__":
    options = parse_args()
    options.install_dir = os.path.abspath(options.install_dir)

    archiver = Archiver(options)
    archive_list = []
    if options.tar:
        print("Generating tar archive")
        archive_list.append(archiver.build_tar())
    if options.zip:
        print("Generating zip archive")
        archive_list.append(archiver.build_zip())

    if options.deploy:
       deployer = Deployer(options)
       deployer.deploy(*archive_list)
