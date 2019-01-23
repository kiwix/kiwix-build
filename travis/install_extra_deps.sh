#!/usr/bin/env bash

set -e

if [[ "$TRAVIS_OS_NAME" == "osx" ]]
then
  pip3 install pillow
  pip3 install .

  wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-mac.zip
  unzip ninja-mac.zip ninja
else
  wget https://bootstrap.pypa.io/get-pip.py
  python3.5 get-pip.py --user
  python3.5 -m pip install --user --upgrade pip wheel
  python3.5 -m pip install --user pillow
  python3.5 -m pip install --user .
  python3.5 -m pip show -f kiwix-build

  wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
  unzip ninja-linux.zip ninja
fi

mkdir -p $HOME/bin
cp ninja $HOME/bin

