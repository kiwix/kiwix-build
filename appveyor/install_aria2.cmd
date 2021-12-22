REM ========================================================
REM Install aria2
curl -fsSL -O https://github.com/aria2/aria2/releases/download/release-1.36.0/aria2-1.36.0-win-64bit-build1.zip || exit /b 1
7z e aria2-1.36.0-win-64bit-build1.zip -o%EXTRA_DIR% aria2-1.36.0-win-64bit-build1\aria2c.exe || exit /b 1
