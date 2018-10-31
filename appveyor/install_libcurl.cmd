REM ========================================================
REM Install libcurl
curl -fsSL -O https://curl.haxx.se/download/curl-7.61.1.zip || exit /b 1
7z x curl-7.61.1.zip || exit /b 1
cd curl-7.61.1\winbuild
nmake /f Makefile.vc mode=static MACHINE=x64 DEBUG=no VC=15 ENABLE_IDN=no || exit /b 1
mkdir %EXTRA_DIR%\include\curl
copy ..\builds\libcurl-vc15-x64-release-static-ipv6-sspi-winssl\include\curl\*.h %EXTRA_DIR%\include\curl
copy ..\builds\libcurl-vc15-x64-release-static-ipv6-sspi-winssl\lib\libcurl_a.lib %EXTRA_DIR%\lib
move %EXTRA_DIR%\lib\libcurl_a.lib %EXTRA_DIR%\lib\libcurl.a
dir %EXTRA_DIR%\include\curl
dir %EXTRA_DIR%\lib
curl -fsSl -o%PKG_CONFIG_PATH%\libcurl.pc http://public.kymeria.fr/KIWIX/windows/libcurl.pc || exit /b 1
cd ..\..
