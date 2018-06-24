#!/bin/sh

if ! test -f kiwix-serve
then
  echo Needs to run in the same directory that hosts kiwix-serve binary.
  exit 1
fi

find -type f | \
while read
do
  if hexdump -C $REPLY | head -1 | grep -q ELF
  then
    mv -iv "$REPLY" "$REPLY.real"
    ln -s run-nonroot "$REPLY"
  fi
done

cat <<'EOF' > run-nonroot
#!/bin/sh

BASENAME=`basename $0`
SCRIPT=`realpath $0`
SCRIPTPATH=`dirname $SCRIPT`

if test x"$BASENAME" != xrun-nonroot
then
  for fullarch in "" ${ARCH_FULL:-mips-linux-gnu}
  do for libdir in usr/lib lib
     do LD_LIBRARY_PATH="${SCRIPTPATH%/bin}/$libdir/$fullarch:$LD_LIBRARY_PATH"
     done
  done

  export LD_LIBRARY_PATH
  exec ${SCRIPTPATH}/$BASENAME.real "$@"
fi
EOF

chmod +x run-nonroot
