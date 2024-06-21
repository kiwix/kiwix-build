REM ========================================================
REM Install xapian
curl -fsSL -O https://public.kymeria.fr/KIWIX/xapian-core-1.4.23.zip || exit /b 1
7z x xapian-core-1.4.23.zip || exit /b 1
cd xapian-core-1.4.23
mkdir build
cd build
%MINGW64_RUN% "cd /c/Projects/kiwix-build/xapian-core-1.4.23/build && /c/Projects/kiwix-build/appveyor/build_xapian.sh" || exit /b 1
cd ..\..
