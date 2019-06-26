REM ========================================================
REM Install kiwix-lib
git clone https://github.com/kiwix/kiwix-tools.git || exit /b 1
cd kiwix-tools
set "CPPFLAGS=-I%EXTRA_DIR%/include"
set "LDFLAGS=-lshlwapi -lwinmm"
meson . build --prefix %EXTRA_DIR% -Dstatic-linkage=true --buildtype release || exit /b 1
cd build
ninja || exit /b 1
ninja install || exit /b 1
cd ..\..
