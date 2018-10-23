REM ========================================================
REM Install kiwix-lib
git clone https://github.com/kiwix/kiwix-lib.git || exit /b 1
cd kiwix-lib
meson . build --prefix %EXTRA_DIR% --default-library static --buildtype release || exit /b 1
cd build
ninja || exit /b 1
ninja install || exit /b 1
cd ..\..
