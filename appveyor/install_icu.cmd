REM ========================================================
REM Install icu
curl -SL -O http://public.kymeria.fr/KIWIX/windows/icu4c-62_1-Win64-MSVC2017.zip || exit /b 1
7z x icu4c-62_1-Win64-MSVC2017.zip -o%EXTRA_DIR% -r include || exit /b 1
7z e icu4c-62_1-Win64-MSVC2017.zip -o%EXTRA_DIR%\lib lib64\* || exit /b 1
7z e icu4c-62_1-Win64-MSVC2017.zip -o%EXTRA_DIR%\bin bin\*.dll || exit /b 1
curl -fsSL -o%PKG_CONFIG_PATH%\icu-i18n.pc http://public.kymeria.fr/KIWIX/windows/icu-i18n.pc || exit /b 1
