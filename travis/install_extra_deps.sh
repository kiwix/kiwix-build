#!/usr/bin/env bash

set -e

orig_dir=$(pwd)

sudo apt-get update -qq
sudo apt-get install -qq python3-pip
pip3 install meson

# ninja
git clone git://github.com/ninja-build/ninja.git
cd ninja
git checkout release
./configure.py --bootstrap
sudo cp ninja /bin

cd $orig_dir

