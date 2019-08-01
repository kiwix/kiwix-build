#!/usr/bin/env python3

import requests
from requests.auth import HTTPBasicAuth
import os, sys
import json

bintray_auth = (os.environ['BINTRAY_USER'], os.environ['BINTRAY_PASS'])


def generate_pom_file(version):
    template = """<?xml version="1.0" encoding="UTF-8"?>
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns="http://maven.apache.org/POM/4.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.kiwix.kiwixlib</groupId>
  <artifactId>kiwixlib</artifactId>
  <version>{version}</version>
  <packaging>aar</packaging>
  <name>kiwixlib</name>
  <description>kiwixlib</description>
  <url>https://github.com/kiwix/kiwix-lib</url>
  <licenses>
    <license>
      <name>GPLv3</name>
      <url>https://www.gnu.org/licenses/gpl-3.0.en.html</url>
    </license>
  </licenses>
  <developers>
    <developer>
      <id>kiwix</id>
      <name>kiwix</name>
      <email>contact@kiwix.org</email>
    </developer>
  </developers>
  <scm>
    <connection>https://github.com/kiwix/kiwix-lib.git</connection>
    <developerConnection>https://github.com/kiwix/kiwix-lib.git</developerConnection>
    <url>https://github.com/kiwix/kiwix-lib</url>
  </scm>
</project>"""
    return template.format(version=version)


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


def upload_archive(version, filename, artefact):
    url_template = "https://api.bintray.com/content/kiwix/kiwix/kiwixlib/{version}/org/kiwix/kiwixlib/kiwixlib/{version}/{artefact}"
    parameters = {
        'publish': 1,
        'override': 1
    }

    # Upload the main artefact
    url = url_template.format(version=version, artefact=artefact)
    with open(filename, 'rb') as f:
        r = requests.put(url, data=f, auth=bintray_auth, params=parameters)

    rcode = r.status_code
    rcode_family = rcode // 100
    if rcode_family not in (2, 3):
        print("ERROR: Fail to upload artefact")
        return False

    # Upload the pom file
    pom_artefact = os.path.splitext(artefact)[0] + ".pom"
    url = url_template.format(version=version, artefact=pom_artefact)
    data = generate_pom_file(version)
    r = requests.put(url, data=data, auth=bintray_auth, params=parameters)

    rcode = r.status_code
    rcode_family = rcode // 100
    if rcode_family not in (2, 3):
       print("ERROR: Fail to upload pom artefact")
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

    filepath = os.path.join(os.path.dirname(sys.argv[1]), options['filename'])
    if not upload_archive(options['version'], filepath, options['artefact']):
         sys.exit("Cannot upload artefact")
