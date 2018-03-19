#!/usr/bin/env bash

set -e

orig_dir=$(pwd)

sudo apt-get update -qq
sudo apt-get install -qq python3-pip zlib1g-dev libjpeg-dev
pip3 install --user --upgrade pip wheel
pip3 install --user pillow meson==0.43.0

# ninja
wget https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-linux.zip
unzip ninja-linux.zip ninja
sudo cp ninja /bin

cd $orig_dir

