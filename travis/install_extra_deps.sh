#!/usr/bin/env bash

set -e

orig_dir=$(pwd)

pip3 install --user --upgrade pip wheel
pip3 install --user pillow meson==0.43.0

# ninja
wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
unzip ninja-linux.zip ninja
cp ninja $HOME/bin

cd $orig_dir

