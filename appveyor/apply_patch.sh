#!/usr/bin/env bash

mydir=$(dirname "$0")
patch -p1 < "$mydir"/../kiwixbuild/patches/"$1"
