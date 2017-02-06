#!/bin/sh


if test -z "$PATH_ORIG" ; then
  PATH_ORIG="$PATH"; export PATH_ORIG;
fi;

PATH="{root_path}/bin:$PATH_ORIG"; export PATH;

HOST_CC=gcc; export HOST_CC;
unset PKG_CONFIG_PATH;

CC={which:{binaries[c]}}; export CC
AR={which:{binaries[ar]}}; export AR
CXX={which:{binaries[cpp]}}; export CXX
STRIP={which:{binaries[strip]}}; export STRIP
CFLAGS=" -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4"; export CFLAGS;
CXXFLAGS=" -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions --param=ssp-buffer-size=4"; export CXXFLAGS;


exec "$@"
