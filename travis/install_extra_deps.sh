#!/usr/bin/env bash

set -e

if [[ "$TRAVIS_OS_NAME" == "osx" ]]
then
  brew update
  brew upgrade python3
  pip3 install pillow
  pip3 install .

  wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-mac.zip
  unzip ninja-mac.zip ninja
else
  pip3 install --user --upgrade pip wheel
  pip3 install --user pillow
  pip3 install --user .

  wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
  unzip ninja-linux.zip ninja
fi

mkdir -p $HOME/bin
cp ninja $HOME/bin

