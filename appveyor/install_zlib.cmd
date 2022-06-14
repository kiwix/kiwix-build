REM ========================================================
REM Install zlib
curl -fsSL -O http://mirror.download.kiwix.org/dev/kiwix-build/zlib-1.2.12.meson.zip || exit /b 1
7z x zlib-1.2.12.meson.zip || exit /b 1
cd zlib-1.2.12
meson . build --prefix %EXTRA_DIR% --default-library static --buildtype release || exit /b 1
cd build
ninja || exit /b 1
ninja install || exit /b 1
cd ..\..
