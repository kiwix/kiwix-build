
XAPIAN_SOURCE=$(pwd)/..

$XAPIAN_SOURCE/configure \
  CC="cl -nologo" \
  CXX="$XAPIAN_SOURCE/compile cl -nologo" \
  CXXFLAGS="-EHsc -MD" AR=lib \
  CPPFLAGS="-I${MINGW64_EXTRA_DIR}/include" \
  LDFLAGS="-L${MINGW64_EXTRA_DIR}/lib" \
  --disable-backend-remote \
  --disable-documentation \
  --prefix=${MINGW64_EXTRA_DIR}

make -j2

make install
