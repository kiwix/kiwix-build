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

from utils import (
    Remotefile,
    download_remote
)

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
google play, using tha 'alpha' track of the application.

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
    parser.add_argument('--zim-url')

    advance = parser.add_argument_group('advance', "Some advanced options.")
    advance.add_argument('--extra-code', type=int, default=0)
    advance.add_argument('--check-certificate', default=True)

    # Hidden options
    parser.add_argument('--step', default='launch', choices=['launch', 'publish'], help=argparse.SUPPRESS)
    parser.add_argument('--apks-dir', help=argparse.SUPPRESS)
    parser.add_argument('--version', default="0", help=argparse.SUPPRESS)
    parser.add_argument('--content-version-code', type=int)
    parser.add_argument('--package-name', default=None, help=argparse.SUPPRESS)
    parser.add_argument('--google-api-key', help=argparse.SUPPRESS)

    options = parser.parse_args()

    if not options.package_name:
        print("Try to get package name from info.json file")
        request_url = ('https://raw.githubusercontent.com/kiwix/kiwix-android-custom/master/{}/info.json'
                      .format(options.custom_app))
        json_request = requests.get(request_url)
        if json_request.status_code != 200:
            print("Error while getting json file.")
            print("Reason is '{}'".format(json_request.reason))
            sys.exit(-1)
        json_data = json.loads(json_request.text)
        print("Found package_name '{}'".format(json_data['package']))
        options.package_name = json_data['package']

    options.base_version = "{}{}".format(
        datetime.date.today().strftime('%y%j'),
        options.extra_code)

    return options


def download_zim_file(zim_url, dest_dir=None):
    if dest_dir is None:
        dest_dir = os.getcwd()
    out_filename = urlparse(zim_url).path
    out_filename = os.path.basename(out_filename)
    zim_file = Remotefile(out_filename, '', zim_url)
    download_remote(zim_file, dest_dir)
    return os.path.join(dest_dir, out_filename)


def get_zim_size(zim_url, check_certificate=True):
    print("Try to get zim size")
    if not check_certificate:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context = None
    extra_args = {'context':context} if sys.version_info >= (3, 4, 3) else {}
    with urllib.request.urlopen(zim_url, **extra_args) as resource:
        size = resource.getheader('Content-Length', None)
    if size is not None:
        size = int(size)
        print("Zim size is {}".format(size))
        return size
    else:
        print("No 'Content-Length' header in http answer from the server.\n"
              "We need to download the zim file to get its size.")
        zim_path = download_zim_file(zim_url, tempfile.gettempdir())
        size = os.path.getsize(zim_path)
        print("Zim size is {}".format(size))
        return size


def do_launch(options):
    zim_size = get_zim_size(options.zim_url, options.check_certificate)
    travis_launch_build('kiwix', 'kiwix-build', options, zim_size)
    print("Travis build has been launch.")


def do_publish(options):
    zim_path = download_zim_file(options.zim_url)
    googleService = Google(options)
    with googleService.new_request():
        versionCodes = []
        for apk in glob.iglob(options.apks_dir+"/*.apk"):
            result = googleService.upload_apk(apk)
            versionCodes.append(result['versionCode'])
        googleService.upload_expansionfile(
            zim_path, options.content_version_code, versionCodes)
        googleService.publish_release(options, versionCodes)


def travis_launch_build(organisation, repository, options, zim_size):
    request_url = tmpl_request_url.format(
        organisation=organisation,
        repository=repository,
        endpoint='requests')
    headers = {
        "Travis-API-Version": "3",
        "Content-Type": "application/json",
        "Authorization": "token {}".format(options.travis_token),
        "User-Agent": "kiwix-build"
    }
    uuid = uuid4()
    envs = []
    for platform_index, platform in enumerate(['arm', 'arm64', 'x86', 'x86_64', 'mips', 'mips64']):
        d = {
            'PLATFORM': "android_{}".format(platform),
            'VERSION_CODE': gen_version_code(platform_index, options.base_version)
        }
        envs.append(d)

    global_env = [
        { 'CUSTOM_APP': options.custom_app},
        { 'ZIM_FILE_SIZE': zim_size},
        { 'PACKAGE_NAME': options.package_name},
        { 'ZIM_URL': options.zim_url},
        { 'EXTRA_CODE': options.extra_code},
        { 'BASE_VERSION': options.base_version},
        { 'CONTENT_VERSION_CODE': gen_version_code(0, options.base_version)},
        { 'VERSION': options.version},
        { 'secure': ('u6MCvCQhAlvU0jNojLVatNXHr6AYj4rjU9CY9JcUUG9CKMsls1t3ERz'
                     'aab0vY1H7EIYl8uMgJcE71lF+61/sVOz7DPJVbKBorivnOlvMvyG2xU'
                     'su/q3ddMcAkuyixtW2Yo7oq8Tug5PbL5qybrZ+TD0BplS/XcpgljMTH'
                     'gxWDYion5Y1/Udz5zg1VIxHGAcv3lKYqtbPzA5gR7scLhFVMVulpFDC'
                     'Ps9MS/jEpwJtHrSZPrRmkOdLCJJNgOnQmRe0ib6NsmhO9KgpeEZRgUx'
                     'bSaOOiXKBwN7MdWHCZKczZbwVBEA9Izw29hVh0fQZpZNuC3GAICydyK'
                     'XmbGLNy+GqIPOJPXbAgfT8zRK2IN+PuUHL0xizK4QALMX1jTiiJ65i1'
                     'vWy1NZ3fS7kbgulPUXvkIs2PoSULVEAqhhanp+1ICcEVKs5ffc3e0WP'
                     '/p7NSTIL8QF58QYPOIqWXX17IP3kfrWURIWCdPHCHKEGkg0S+HyqKa6'
                     '/pdR5CeBCeECLraupzJ+ZfKIfsFFyrOgCWRYe1pIAD5C1f/0jM6T+9h'
                     'Vsc2ktgjM8GpujTztzMKNrVJ80mNBtdXbFGYn01B/zhVSsxPIrbROVp'
                     '5UL/lFxJVPIrSe2nIs4AFhanhSDK5ro9qCI6GotPqhyd+RhuJMY/p36'
                     'fs/srp3KL+aNd8JFxWj45M0=') },
        { 'secure': ('xotOZyUbkcgoZhS4ZAaNtqaxhxRV03rgWRSxaccI+INczLNK18xiVUj'
                     'I/1zdAil+ck8rXDMYVuXGo860UIaxt7Sxa7j24+nu6KNpDmlB2a1xyd'
                     'Ls8RNL9tUpx4t+DooTHmUuUJSipUcchK6ZRAKFYOHB9Lumkbz2H2Ifs'
                     'U1AYnLZfcGC7U63DojGFYJmgXwCgHJ25Zq00SCYdHq1b5vpvQ3ZVviI'
                     '0+OTXCK804sSiLu3g6EamsQn7+P5F4RnMrKtm6kP2iTZ3sbED6L6adA'
                     'mtOWKDfgrMIbYO3kgYemfNE12KG+Lfey10RiheC/CbUZHV3jSl+LE1z'
                     'hY8Nqcf6rYQZ8QceE9gW53MrILpUxi7oSltR/pwenNNS5uEox1SrMtY'
                     '2/O0K0dixHHgF96RV5YuqJQurzTEXTt4T9Uu1ZItp3rauSwcj6wbTYu'
                     'fWnGeUzNVItZkSruysBY5mrcvkH6lQpCMk5x6kAzvHCQM4DtIWcep3P'
                     'LG0lj034OuZc7MxIh9GzReeYw/gawF2xEgmiitlBaPVvYUff0BaJ8K7'
                     'R0bbbYOuIibxrXsiAIZwa0d9vS2PBoerORD/hiE3QD+c0o3uEn8btw+'
                     'pebokk6SizfS1q44tcWWRpaovm8uD3rhJ0alm6Ht0V7ErGzXafAzsiR'
                     'B/o4trHiAeJUJuSIKDyvmWk=') }
    ]

    env = {
        'matrix': envs,
        'global': global_env
    }

    data = {
        'request': {
             'message' : tmpl_message.format(app=options.custom_app, zim=options.zim_url, uuid=uuid),
             'branch'  : "custom_app",
             'config'  : {
                 'before_install' : [
                     ( 'pip3 install pyOpenSSl google-api-python-client'
                       ' httplib2 apiclient requests'),
                     ( 'openssl aes-256-cbc -k $google_key'
                       ' -in travis/googleplay_android_developer-5a411156212c.json.enc'
                       ' -out travis/googleplay_android_developer-5a411156212c.json'
                       ' -d'),
                     ( 'openssl aes-256-cbc -k $google_key'
                       ' -in travis/test_ks.ks.enc'
                       ' -out travis/test_ks.ks -d'),
                     ( 'openssl aes-256-cbc -K $encrypted_eba2f7543984_key'
                       ' -iv $encrypted_eba2f7543984_iv'
                       ' -in travis/travisci_builder_id_key.enc'
                       ' -out travis/travisci_builder_id_key -d'),
                     'chmod 600 travis/travisci_builder_id_key'
                 ],
                 'env' : env,
                 'script' : 'travis_wait 30 travis/compile_custom_app.sh',
                 'deploy' : {
                      'provider': 'script',
                      'skip_cleanup': True,
                      'script': 'travis/deploy_apk.sh',
                      'on': {
                          'branch': 'custom_app'
                      }
                 },
                 'jobs': {
                     'include': [
                         {
                             'stage' : 'make_release',
                             'install': 'pip3 install -r requirements_build_custom_app.txt',
                             'script': True,
                             'env': global_env,
                             'deploy' : {
                                 'provider': 'script',
                                 'skip_cleanup': True,
                                 'script': 'travis/make_release.sh',
                                 'on': {
                                     'branch': 'custom_app'
                                 }
                             }
                         }
                     ]
                 }
             }
        }
    }


    r = requests.post(request_url, headers=headers, json=data)
    if r.status_code != 202:
        print("Error while requesting build:")
        print(r.reason)
        print("Have you forget to give the travis token ?")
        sys.exit(-1)
    else:
        request_id = r.json()['request']['id']
        print("Request {} has been schedule.".format(request_id))
        request_left = 10
        found = False
        request_url = tmpl_request_url.format(
            organisation=organisation,
            repository=repository,
            endpoint='builds')
        while request_left:
            time.sleep(1)
            print("Try to get associated build.")
            r = requests.get(request_url, headers=headers)
            json_data = json.loads(r.text)
            for build in json_data['builds']:
                if build['event_type'] != 'api':
                    continue
                message = build['commit']['message']
                if str(uuid) in message:
                    found = True
                    break
            if found:
                break
            print("Cannot find build. Wait 1 second and try again")
            print("{} tries left".format(request_left))
            request_left -= 1
        if found:
            print("Associated build found:  {}.".format(build['number']))
            print("https://travis-ci.org/kiwix/kiwix-build/builds/{}".format(build['id']))
        else:
            print("Request has been accepted by travis-ci but I cannot found "
                  "the associated build. Have a look here "
                  "https://travis-ci.org/kiwix/kiwix-build/builds"
                  "if you found it.")


ERROR_MSG_EDIT_CHANGE = "A change was made to the application outside of this Edit, please create a new edit."

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

    def upload_expansionfile(self, comp_file, contentVersionCode, versionCodes):
        versionCodes = [int(v) for v in versionCodes]
        self.make_request('expansionfiles', 'upload',
            expansionFileType='main',
            apkVersionCode=contentVersionCode,
            media_body=comp_file,
            media_mime_type='application/octet-stream')
        for versionCode in versionCodes:
            if versionCode == contentVersionCode:
                continue
            self.make_request('expansionfiles', 'update',
                expansionFileType='main',
                apkVersionCode=versionCode,
                body={'referencesVersion': contentVersionCode}
            )

    def upload_apk(self, apk_file):
        return self.make_request('apks', 'upload',
            media_body=apk_file)

    def publish_release(self, options, versionCodes):
        return self.make_request('tracks', 'update',
            track="alpha",
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
