REM ========================================================
REM Install pthread
curl -fsSL -O ftp://sourceware.org/pub/pthreads-win32/pthreads-w32-2-9-1-release.zip || exit /b 1
7z x pthreads-w32-2-9-1-release.zip -r pthreads.2 || exit /b 1
cd pthreads.2
REM Patch is pthread_timespec.patch
curl -fsSL -O http://public.kymeria.fr/KIWIX/windows/pthread.h || exit /b 1
nmake clean VC-inlined || exit /b 1
copy pthread.h %EXTRA_DIR%\include
copy sched.h %EXTRA_DIR%\include
copy pthreadVC2.lib %EXTRA_DIR%\lib
copy pthreadVC2.dll %EXTRA_DIR%\bin
curl -fsSL -o%PKG_CONFIG_PATH%\libpthreadVC2.pc http://public.kymeria.fr/KIWIX/windows/libpthreadVC2.pc || exit /b 1
cd ..
