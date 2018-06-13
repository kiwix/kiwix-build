REM ========================================================
REM Install xapian
curl -fsSL -O http://public.kymeria.fr/KIWIX/windows/xapian-core-1.5.0.zip || exit /b 1
7z x xapian-core-1.5.0.zip || exit /b 1
cd xapian-core-1.5.0
mkdir build
cd build
%MINGW64_RUN% "cd /c/Projects/kiwix-build/xapian-core-1.5.0/build && /c/Projects/kiwix-build/appveyor/build_xapian.sh" > build_xapian.log || exit /b 1
cd ..\..
