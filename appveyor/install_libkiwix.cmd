REM ========================================================
REM Install libkiwix
git clone https://github.com/kiwix/libkiwix.git || exit /b 1
cd libkiwix
git checkout iframe_based_content_viewer || exit /b 1
set CPPFLAGS="-I%EXTRA_DIR%/include"
meson . build --prefix %EXTRA_DIR% --default-library static --buildtype release || exit /b 1
cd build
ninja || exit /b 1
ninja install || exit /b 1
cd ..\..
