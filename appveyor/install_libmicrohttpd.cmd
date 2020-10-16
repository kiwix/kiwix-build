REM ========================================================
REM Install libmicrohttpd
curl -fsSL -O https://ftpmirror.gnu.org/libmicrohttpd/libmicrohttpd-latest-w32-bin.zip || exit /b 1
7z e libmicrohttpd-latest-w32-bin.zip -o%EXTRA_DIR%/include libmicrohttpd-*-w32-bin/x86_64/VS2019/Release-static/microhttpd.h || exit /b 1
7z e libmicrohttpd-latest-w32-bin.zip -o%EXTRA_DIR%/lib libmicrohttpd-*-w32-bin/x86_64/VS2019/Release-static/libmicrohttpd.lib || exit /b 1
7z e libmicrohttpd-latest-w32-bin.zip -o%EXTRA_DIR%/lib/pkgconfig libmicrohttpd-*-w32-bin/x86_64/MinGW/static/mingw64/lib/pkgconfig/* || exit /b 1

rename %EXTRA_DIR%\lib\libmicrohttpd.lib microhttpd.lib
dir %EXTRA_DIR%
dir %EXTRA_DIR%\lib
dir %EXTRA_DIR%\lib\pkgconfig
