#!/usr/bin/env python3

import os, sys
import json
import requests

bintray_auth = (os.environ['BINTRAY_USER'], os.environ['BINTRAY_PASS'])

def create_version(version):
    url = "https://api.bintray.com/packages/kiwix/kiwix/kiwixlib/versions"
    payload = {
        'name': version,
        'desc': 'Release of kiwix-lib'
    }
    headers = {
        'Content-Type': 'application/json'
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers, auth=bintray_auth)
    rcode = r.status_code

    if rcode == 409:
        print("Bintray version %s already exists, skipping." % version)
        return True

    rcode_family = rcode // 100
    if rcode_family in (2, 3):
        print("Bintray Version created!")
        return True

    print("ERROR : Bintray API response {}".format(rcode))
    return False


def upload(version, filepath, artefact):
    url_template = "https://api.bintray.com/content/kiwix/kiwix/kiwixlib/{version}/org/kiwix/kiwixlib/kiwixlib/{version}/{artefact}"
    parameters = {
        'publish': 1,
        'override': 1
    }

    # Upload the main artefact
    url = url_template.format(version=version, artefact=artefact)
    with open(filepath, 'rb') as f:
        r = requests.put(url, data=f, auth=bintray_auth, params=parameters)

    rcode = r.status_code
    rcode_family = rcode // 100
    if rcode_family not in (2, 3):
        print("ERROR: Fail to upload artefact")
        print(r.text)
        return False

    return True



if __name__ == "__main__":
    try:
        info_file = sys.argv[1]
    except IndexError:
        print("Usage {} infofile".format(sys.argv[0]))
        sys.exit(-1)

    print("Use info file {}".format(info_file))
    with open(info_file) as f:
        options = json.load(f)

    if not create_version(options['version']):
        sys.exit("Cannot create version")

    basedir = os.path.dirname(sys.argv[1])
    for file_ in options['files']:
        path = os.path.join(basedir, file_)
        if not upload(options['version'], path, file_):
            sys.exit("Cannot upload file {}".format(file_))
