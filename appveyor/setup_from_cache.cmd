REM ========================================================
REM Setup from cache
curl -fsSL -O http://tmp.kiwix.org/ci/deps_windows_windows.zip || exit /b 1
7z x deps_windows_windows.zip -oc: -aoa || exit /b 1
