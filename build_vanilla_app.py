#!/usr/bin/env python3

import \
    argparse, \
    datetime, \
    glob, \
    json, \
    os, \
    ssl, \
    sys, \
    tempfile, \
    time, \
    urllib
from uuid import uuid4
from contextlib import contextmanager
from urllib.parse import urlparse

import requests
import httplib2
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client import client
from oauth2client.service_account import ServiceAccountCredentials

tmpl_request_url = "https://api.travis-ci.org/repo/{organisation}%2F{repository}/{endpoint}"
tmpl_message = """Build of custom app {app} with zim file {zim}.

UUID:#{uuid}#"""

description = """Launch a custom application build.
This command will launch a custom application build on Travis-CI.
Travis-CI jobs will compile the application and upload the build apks on
google play, using tha 'internal test' track of the application.

You will need to have a valid TRAVIS_TOKEN associated to your personnal account
and the kiwix-build repository on travis.
Use the 'travis' command line tool (https://github.com/travis-ci/travis.rb)
to generate a token.
"""

def parse_args():
    parser = argparse.ArgumentParser(description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--custom-app')
    parser.add_argument('--travis-token')

    advance = parser.add_argument_group('advance', "Some advanced options.")
    advance.add_argument('--extra-code', type=int, default=0)
    advance.add_argument('--version-name', default=None,
                         help="The version of the application (seen by user). Get from json info file by default.")
    advance.add_argument('--check-certificate', default=True)
    advance.add_argument('--no-android-upload', action='store_false', dest='android_upload')

    # Hidden options
    parser.add_argument('--step', default='launch', choices=['launch', 'publish'], help=argparse.SUPPRESS)
    parser.add_argument('--apks-dir', help=argparse.SUPPRESS)
    parser.add_argument('--google-api-key', help=argparse.SUPPRESS)

    options = parser.parse_args()
    options.package_name = "org.kiwix.kiwixmobile"

    options.base_version = "{}{}".format(
        datetime.date.today().strftime('%y%j'),
        options.extra_code)

    return options

def do_publish(options):
    googleService = Google(options)
    with googleService.new_request():
        versionCodes = []
        for apk in glob.iglob(options.apks_dir+"/*.apk"):
            result = googleService.upload_apk(apk)
            versionCodes.append(result['versionCode'])
        googleService.publish_release(options, versionCodes)


class Google:
    def __init__(self, options):
        scope = 'https://www.googleapis.com/auth/androidpublisher'
        key = options.google_api_key
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            key,
            scopes=[scope])

        http = httplib2.Http()
        http = credentials.authorize(http)

        self.service = build('androidpublisher', 'v2', http=http)
        self.packageName = options.package_name
        self.edit_id = None

    @contextmanager
    def new_request(self):
        edit_request = self.service.edits().insert(
            packageName=self.packageName,
            body={})
        result = edit_request.execute()
        print("create", result)
        self.edit_id = result['id']

        yield

        commit_request = self.service.edits().commit(
            editId=self.edit_id,
            packageName=self.packageName)
        result = commit_request.execute()
        print("commit", result)

        self.edit_id = None

    def make_request(self, section, method, **kwargs):
        request_content = self._build_request_content(kwargs)
        _section = getattr(self._edits, section)()
        _method = getattr(_section, method)
        print(">", request_content)
        request = _method(**request_content)
        result = request.execute()
        print("<", result)
        return result

    def _build_request_content(self, kwargs):
        d = kwargs.copy()
        d['editId'] = self.edit_id
        d['packageName'] = self.packageName
        return d

    @property
    def _edits(self):
        return self.service.edits()

    def upload_apk(self, apk_file):
        return self.make_request('apks', 'upload',
            media_body=apk_file)

    def publish_release(self, options, versionCodes):
        return self.make_request('tracks', 'update',
            track="internal",
            body={'versionCodes': versionCodes})


def gen_version_code(platform_index, base_version):
    str_version = "{platform}{base_version}".format(
        platform=platform_index,
        base_version=base_version
    )
    return int(str_version)

if __name__ == "__main__":
    options = parse_args()
    func = globals()['do_{}'.format(options.step)]
    func(options)
