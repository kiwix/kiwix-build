REM ========================================================
REM Install zlib
curl -fsSL -O http://public.kymeria.fr/KIWIX/windows/zlib-1.2.11.meson.zip || exit /b 1
7z x zlib-1.2.11.meson.zip || exit /b 1
cd zlib-1.2.11
meson.py . build --prefix %EXTRA_DIR% --default-library static --buildtype release || exit /b 1
cd build
ninja || exit /b 1
ninja install || exit /b 1
cd ..\..
