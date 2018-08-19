REM ========================================================
REM Install lzma
curl -fsSL -O https://tukaani.org/xz/xz-5.2.4-windows.zip || exit /b 1
7z x xz-5.2.4-windows.zip -o%EXTRA_DIR% -r include || exit /b 1
7z e xz-5.2.4-windows.zip -o%EXTRA_DIR%\lib bin_x86-64\liblzma.a || exit /b 1
curl -fsSL -o%PKG_CONFIG_PATH%\liblzma.pc http://public.kymeria.fr/KIWIX/windows/liblzma.pc || exit /b 1
