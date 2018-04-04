#!/usr/bin/env bash

set -e

pip3 install --user --upgrade pip wheel
pip3 install --user pillow

pip3 install --user .

# ninja
wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
unzip ninja-linux.zip ninja
cp ninja $HOME/bin

