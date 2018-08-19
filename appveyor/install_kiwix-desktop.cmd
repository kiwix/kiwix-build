REM ========================================================
REM Install kiwix-desktop
git clone https://github.com/kiwix/kiwix-desktop || exit /b 1
cd kiwix-desktop
echo "Getting fix_desktop"
curl -fsSL -O http://public.kymeria.fr/KIWIX/windows/fix_desktop_makefile.py_ || exit /b 1
echo "Running qmake"
C:\Qt\5.11\msvc2017_64\bin\qmake.exe || exit /b 1
echo "Running fix_desktop"
C:\Python36\Python fix_desktop_makefile.py_ Makefile.Release || exit /b 1
echo "Running nmake"
nmake || exit /b 1
cd ..
