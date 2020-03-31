REM ========================================================
REM Install zstd
curl -fsSL -o zstd-v1.4.4.zip https://github.com/facebook/zstd/archive/v1.4.4.zip || exit /b 1
7z x zstd-v1.4.4.zip || exit /b 1
cd zstd-1.4.4/build/meson
meson . builddir --prefix %EXTRA_DIR% --default-library static --buildtype release -Dbin_programs=false -Dbin_contrib=false || exit /b 1
cd builddir
ninja || exit /b 1
ninja install || exit /b 1
cd ..\..\..\..
