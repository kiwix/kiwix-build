REM Set VC 2017
"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat"
mkdir C:\extra\bin
cd C:\projects
C:\Python36\Scripts\pip install meson || exit /b 1

REM Set ninja
curl -fsSL -o ninja-win.zip https://github.com/ninja-build/ninja/releases/download/v1.8.2/ninja-win.zip || exit /b 1
7z e ninja-win.zip -o%EXTRA_DIR%\bin || exit /b 1

REM Set pkg-config-lit
curl -fsSL -o pkg-config-lite-0.28-1.zip https://netix.dl.sourceforge.net/project/pkgconfiglite/0.28-1/pkg-config-lite-0.28-1_bin-win32.zip || exit /b 1
7z e pkg-config-lite-0.28-1.zip -o%EXTRA_DIR%\bin pkg-config-lite-0.28-1/bin/pkg-config.exe || exit /b 1
cd kiwix-build
