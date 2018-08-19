REM ========================================================
REM Install pugixml
curl -fsSL -O http://public.kymeria.fr/KIWIX/windows/pugixml-1.2-meson.zip || exit /b 1
7z x pugixml-1.2-meson.zip -o. || exit /b 1
cd pugixml-1.2-meson
meson.py . build --prefix %EXTRA_DIR% --default-library static --buildtype release || exit /b 1
cd build
ninja || exit /b 1
ninja install || exit /b 1
cd ..\..
