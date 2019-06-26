REM ========================================================
REM Install getopt
curl -fsSL -O https://github.com/takamin/win-c/archive/v1.0.zip || exit /b 1
7z x v1.0.zip -o. || exit /b 1
cd win-c-1.0
mkdir build
cd build
cmake -G"NMake Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=%EXTRA_DIR% .. || exit /b 1
dir
nmake install || exit /b 1
copy ..\include\getopt.h %EXTRA_DIR%\include
cd ..\..

dir %EXTRA_DIR%\include
dir %EXTRA_DIR%\lib
